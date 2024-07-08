from pymilvus import (
    utility,
    connections,
    CollectionSchema,
    FieldSchema,
    DataType,
    Collection,
)
import yaml

# import logging
from common.log import logger
import os
from openai import OpenAI
from typing import List
import asyncio, json
from tenacity import retry, stop_after_attempt, wait_exponential

openai_engine = "text-embedding-ada-002"
VECTOR_DIMENSION = 1536
client = OpenAI()

# MilvusConfPath = os.path.join(os.path.dirname(__file__), "..", "config", "vecdb")

MilvusDType = {
    "INT64": DataType.INT64,
    "INT32": DataType.INT32,
    "INT16": DataType.INT16,
    "INT8": DataType.INT8,
    "BOOL": DataType.BOOL,
    "VARCHAR": DataType.VARCHAR,
    "FLOAT": DataType.FLOAT,
    "DOUBLE": DataType.DOUBLE,
    "JSON": DataType.JSON,
    #'ARRAY': DataType.ARRAY,
    "FLOAT_VECTOR": DataType.FLOAT_VECTOR,
    "BINARY_VECTOR": DataType.BINARY_VECTOR,
}


class MilvusWrapper(Collection):
    def __init__(
        self,
        name,
        schema,
        using="default",
        consistence_level="Strong",
        shards_num=2,
        auto_vectorized_fields=[],
        search_config={},
        index_config={},
        create_index=False,
        hide_keys=False,
    ) -> None:
        if utility.has_collection(name):
            logger.info(f"Loading from exsisting collection {name}.")
        else:
            logger.info(f"Creating new collection {name}")

        super().__init__(
            name=name,
            schema=schema,
            using=using,
            shards_num=shards_num,
            consistency_level=consistence_level,
        )

        self.search_config = search_config
        self.index_config = index_config

        if create_index and self.index_config != {}:
            self.create_index(**list(self.index_config.values())[0])

        self.fields = [f.name for f in schema.fields]
        self.auto_vectorized_fields = auto_vectorized_fields

        self.show_fields = self.fields[: (len(self.fields) - len(self.auto_vectorized_fields))]
        if hide_keys:
            self.show_fields.remove(self.primary_field.name)
        # print(self.show_fields)
        assert len(self.auto_vectorized_fields) <= 1
        self.auto_vec_index = [self.fields.index(field) for field in self.auto_vectorized_fields]

    # data format transfer functions
    def _dicts_to_input_list(self, dict_data):
        if isinstance(dict_data, list) and all(isinstance(jd, dict) for jd in dict_data):
            return [[jd[key] for jd in dict_data] for key in dict_data[0]]
        return [[v] for k, v in dict_data.items()]

    def _lists_to_input_list(self, list_data):
        if isinstance(list_data, list) and all(isinstance(ld, list) for ld in list_data):
            return [[ld[i] for ld in list_data] for i in range(len(list_data[0]))]
        return [[v] for v in list_data]

    def _objects_to_dict(self, obj):
        if isinstance(obj, list):
            return [x.__dict__ for x in obj]
        return obj.__dict__

    def _reformat(self, data):
        if isinstance(data, dict):
            return self._dicts_to_input_list(data)
        elif isinstance(data, list):
            if isinstance(data[0], (int, str)):
                return self._lists_to_input_list(data)
            else:
                assert all(isinstance(element, type(data[0])) for element in data)
                if isinstance(data[0], dict):
                    return self._dicts_to_input_list(data)
                elif isinstance(data[0], list):
                    return self._lists_to_input_list(data)
                return self._dicts_to_input_list(self._objects_to_dict(data))
        return self._dicts_to_input_list(self._objects_to_dict(data))

    def _reformat_and_vectorize(self, data):
        data = self._reformat(data)
        for index, _ in zip(self.auto_vec_index, self.auto_vectorized_fields):
            text = data[index]
            vector = self._get_embedding_for_text(text)
            data.append(vector)
        return data

    @retry(
        stop=stop_after_attempt(5),
        reraise=True,
        wait=wait_exponential(multiplier=1, min=1, max=10),
    )
    def _get_embedding_for_text(self, text: List[str]):
        embeddings = client.embeddings.create(input=text, model=openai_engine, encoding_format="float")
        return [x.embedding for x in embeddings.data]

    def _primary_field_query(self, key, output_fields):
        self.load()
        if self.primary_field.dtype == DataType.VARCHAR:
            expr = f'{self.primary_field.name} == "{key}"'
        else:
            expr = f"{self.primary_field.name} == {key}"
        res = self.query(expr=expr, output_fields=output_fields, consistency_level="Strong")
        return res

    def __setitem__(self, key, value):
        # automatically add key field into data
        if isinstance(value, list):
            assert len(value) < len(self.fields)
            value = [key, *value]
        elif isinstance(value, dict):
            assert self.primary_field.name not in value
            value = {f"{self.primary_field.name}": key, **value}
        else:
            assert self.primary_field.name not in self._objects_to_dict(value)
            value = {f"{self.primary_field.name}": key, **self._objects_to_dict(value)}
        return self.upsert_data(value)

    def __getitem__(self, key):
        res = self._primary_field_query(key, ["*"])
        return {f: res[0][f] for f in self.show_fields}

    def __contains__(self, key):
        res = self._primary_field_query(key, [])
        return res != []

    def keys(self):
        self.load()
        count = self.__len__()
        if count > 0:
            res = self.query(expr="", output_fields=[], limit=count, consistency_level="Strong")
            return [x[f"{self.primary_field.name}"] for x in res]
        return []

    def items(self):
        self.load()
        count = self.__len__()
        if count > 0:
            res = self.query(expr="", output_fields=["*"], limit=count, consistency_level="Strong")
            return [{f: x[f] for f in self.show_fields} for x in res]
        return []

    def __len__(self):
        res = self.query(expr="", output_fields=["count(*)"], consistency_level="Strong")
        return res[0]["count(*)"]

    def remove(self, key):
        if self.primary_field.dtype == DataType.VARCHAR:
            expr = f"{self.primary_field.name} == '{key}'"
        else:
            expr = f"{self.primary_field.name} == {key}"
        self.delete(expr)

    # input: list, obj, json, list[list], list[obj], list[json]
    def insert_data(self, data):
        data = self._reformat_and_vectorize(data)
        return self.insert(data)

    def upsert_data(self, data):
        data = self._reformat_and_vectorize(data)
        # dict_data = {f: data[i] for i, f in enumerate(self.fields)}
        return self.upsert(data)

    def get_search_config(self, name):
        if name in self.search_config:
            return self.search_config[name]
        raise KeyError(f"Search config named {name} does not exist.")

    def search_via_config(self, data, name=None):
        self.load()
        if self.search_config == {}:
            raise RuntimeError("Search configuration is empty.")
        name = name or next(iter(self.search_config))
        if name not in self.search_config:
            raise KeyError(f"Search config named {name} does not exist.")
        if self.search_config[name].get("auto_vectorize", False):
            data = self._get_embedding_for_text(data)
        res = self.search(data, **self.search_config[name]["search_params"])
        return [
            [{f: hit.entity.get(f) for f in self.search_config[name]["search_params"]["output_fields"]} for hit in hits]
            for hits in res
        ]

    def index_via_config(self, name=None):
        if self.index_config == {}:
            raise RuntimeError("Index configuration is empty.")
        name = name or next(iter(self.index_config))
        if name not in self.index_config:
            raise KeyError(f"Index config named {name} does not exist.")
        return self.create_index(**self.index_config[name])


class ConfigMilvusWrapper(MilvusWrapper):
    def __init__(self, config_path, name_modify=None, connection_modify=None) -> None:
        # config_path = os.path.join(MilvusConfPath, config_path)
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        if name_modify != None:
            self.config["name"] = name_modify

        # config for schemas
        schema_config = self.config["collectionSchema"]
        fields = []
        auto_vectorized_fields = []
        for field_config in schema_config["fields"]:
            field_config = self._adapt_field_config(field_config)
            if field_config.pop("auto_vectorize", False):
                auto_vectorized_fields.append(field_config["name"])
            field_schema = FieldSchema(**field_config)
            fields.append(field_schema)

        # adding auto-vectorized fields
        for field_name in auto_vectorized_fields:
            vec_field_name = field_name + "_vec"
            field_schema = FieldSchema(
                **{
                    "name": vec_field_name,
                    "dtype": DataType.FLOAT_VECTOR,
                    "dim": VECTOR_DIMENSION,
                }
            )
            fields.append(field_schema)

        schema_config["fields"] = fields
        schema = CollectionSchema(**schema_config)

        # config for database connection
        conn = connection_modify or self.config["using"]

        # config for search
        search_config = {}
        if "search" in self.config:
            search_config = {d.pop("name"): d for d in self.config["search"]}

        # config for index
        index_config = {}
        if "index" in self.config:
            index_config = {d.pop("name"): d for d in self.config["index"]}

        hide_keys = self.config.get("hide_keys", False)

        super().__init__(
            name=self.config["name"],
            schema=schema,
            using=conn,
            shards_num=self.config["shards_num"],
            consistence_level=self.config.get("consistence_level", "Strong"),
            search_config=search_config,
            index_config=index_config,
            create_index=self.config.get("auto_create_index", True),
            auto_vectorized_fields=auto_vectorized_fields,
            hide_keys=hide_keys,
        )

    def _adapt_field_config(self, field_dict):
        field_dict["dtype"] = MilvusDType[field_dict["dtype"]]
        if "element_type" in field_dict:
            field_dict["dtype"] = MilvusDType[field_dict["element_type"]]
        return field_dict


# connections.connect(
#         alias="default",
#         user='username',
#         password='password',
#         host='localhost', #'host.docker.internal',
#         port='19530'
#     )
