from __future__ import annotations
from sqlitedict import SqliteDict, decode, encode, identity
import os
from abc import ABC, abstractmethod
from typing import Union, Type
from pydantic import BaseModel


class Serializable(ABC):
    @abstractmethod
    def to_dict(self) -> dict:
        raise NotImplementedError("Subclasses must implement this method")

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> Serializable:
        raise NotImplementedError("Subclasses must implement this method")

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.to_dict() == other.to_dict()
        return False


class AutoStoredDict(SqliteDict):
    """
    A dictionary-like interface providing an automatic way to store and retrieve
    objects that are instances of Serializable or BaseModel directly from a SQLite database.
    This class extends SqliteDict to handle complex objects by serializing them before storing
    and deserializing them when retrieving.

    The AutoStoredDict is particularly useful for applications that require persistence
    of complex data structures that go beyond simple key-value pairs, allowing
    efficient storage and retrieval of models and data objects directly from the database.

    Attributes:
        object_type (Type[Union[Serializable, BaseModel]] | None): Specifies the type of objects
            this dictionary will manage. This type must either be a subclass of Serializable or a
            subclass of BaseModel, which are used to perform the correct serialization and
            deserialization operations. If None, the dictionary will manage simple data types that
            do not require serialization or deserialization (e.g., int, str, float, dict).

    Args:
        filename (str): The path to the SQLite database file.
        tablename (str): The name of the table within the database to store the dictionary items.
        object_type (Type[Union[Serializable, BaseModel]] | None, optional): The class type of the objects
            to be stored, which must include serialization and deserialization methods. If set to None, the
            dictionary will handle only simple data types directly (such as int, str, float, dict), which do
            not require complex serialization or deserialization processes. Defaults to None.
        from_dict_hook : Custom hook to define the way of deserialization. Defaults to None.
        **kwargs: Additional keyword arguments to be passed to the SqliteDict constructor.

    Examples:
        # Importing necessary classes
        >>> from pydantic import BaseModel

        # Define a Pydantic model
        >>> class MyModel(BaseModel):
        >>>     name: str
        >>>     age: int

        # Define a class that implements the Serializable interface
        >>> class MySerializable(Serializable):
        >>>     def __init__(self, data):
        >>>         self.data = data
        >>>     def to_dict(self) -> dict:
        >>>         return {"data": self.data}
        >>>     @classmethod
        >>>     def from_dict(cls, data: dict) -> 'MySerializable':
        >>>         return cls(data['data'])
        >>>     def __str__(self):
        >>>         return f"MySerializable(data={self.data})"

        # Create an instance of AutoStoredDict for MyModel
        >>> db_model = AutoStoredDict(filename='mydatabase.sqlite', tablename='mymodels', object_type=MyModel)
        >>> db_model['alice'] = MyModel(name='Alice', age=30)
        >>> print(db_model['alice'])
        MyModel(name='Alice', age=30)

        # Create an instance of AutoStoredDict for MySerializable
        >>> db_serializable = AutoStoredDict(filename='mydatabase.sqlite', tablename='mydata', object_type=MySerializable)
        >>> db_serializable['item1'] = MySerializable("Example data")
        >>> print(db_serializable['item1'])
        MySerializable(data=Example data)
    """

    def __init__(
        self,
        filename: str,
        tablename: str,
        object_type: Type[Union[Serializable, BaseModel]] | None = None,
        from_dict_hook=None,
        **kwargs,
    ):
        self.object_type = object_type
        self.from_dict_hook = from_dict_hook
        os.makedirs(os.path.dirname(filename.rstrip("/")), exist_ok=True)
        super().__init__(filename, tablename, flag="c", autocommit=True, **kwargs)

    def keys(self):
        return [x for x in self.iterkeys()]

    def values(self):
        return [self.__getitem__(key) for key in self.iterkeys()]

    def items(self):
        return [(key, self.__getitem__(key)) for key in self.iterkeys()]

    def __setitem__(self, key, value):
        # return super().__setitem__(key, value)
        if isinstance(value, Serializable):
            super().__setitem__(key, value.to_dict())
        elif isinstance(value, BaseModel):
            super().__setitem__(key, value.model_dump())
        else:
            super().__setitem__(key, value)

    def __getitem__(self, key):
        item = super().__getitem__(key)
        if isinstance(item, dict) and self.object_type:
            if issubclass(self.object_type, BaseModel):
                if self.from_dict_hook != None:
                    return self.from_dict_hook(item)
                else:
                    return self.object_type.model_validate(item)
            elif issubclass(self.object_type, Serializable):
                if self.from_dict_hook != None:
                    return self.from_dict_hook(item)
                else:
                    return self.object_type.from_dict(item)
        return item

    def todict(self):
        return {k: v for k, v in self.iteritems()}

    def __str__(self):
        return str(self.todict())

    def __eq__(self, other):
        if isinstance(other, AutoStoredDict):
            return self.todict() == other.todict()
        return False


class AutoStoredSet:
    def __init__(self, filename, tablename, set_name="__set") -> None:
        self.dbdict = AutoStoredDict(filename, tablename)
        self.set_name = set_name
        if set_name in self.dbdict:
            # print('loading')
            self.data = self.dbdict[f"{self.set_name}"]
        else:
            # print('creating')
            self.data = set()
            self.dbdict[f"{set_name}"] = set()

    def save_db(self):
        self.dbdict[f"{self.set_name}"] = self.data

    def load_db(self):
        self.data = self.dbdict[f"{self.set_name}"]

    def add(self, item):
        self.load_db()
        self.data.add(item)
        self.save_db()

    def remove(self, item):
        self.load_db()
        self.data.remove(item)
        self.save_db()

    def clear(self):
        self.data.clear()
        self.save_db()

    def discard(self, item):
        self.load_db()
        self.data.discard(item)
        self.save_db()

    def __eq__(self, value) -> bool:
        self.load_db()
        return self.data == value

    def __contains__(self, value):
        self.load_db()
        return value in self.data

    def __iter__(self):
        self.load_db()
        return iter(self.data)

    def __str__(self) -> str:
        self.load_db()
        return str(self.data)

    def replace(self, other):
        self.data = set(other)
        self.save_db()
