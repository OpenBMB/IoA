import requests
import os
import json
import concurrent.futures as conf
import traceback

# import copy


def run(input_item: dict):
    """
    input_item: dict, including the keys 'instruction'
    """
    goal = input_item["instruction"]
    try:
        response = requests.post(
            "http://127.0.0.1:5050/launch_goal",
            json={
                "goal": goal,
                "team_member_names": ["AutoGPT", "Open Interpreter"],
                # "team_up_depth": 1,  # the depth limit of nested teaming up
                "max_turns": 40,
            },
        )
        print(response.text)

        plain_text = response.text
        new_item = input_item.copy()
        new_item["plain_text"] = plain_text
        try:
            comm_id, conclusion = response.json()
            new_item["conclusion"] = conclusion
            new_item["task_id"] = comm_id
        except Exception as e:
            print(f"inner error while converting to json...: {e}")
        return new_item
    except Exception as e:
        print(f"error: {e}...")
        traceback.print_exc()
        return None


def run_concurrently(data: list[dict], appendFilePath: str, flag_key: str = "flag", max_workers: int = 5):
    if not os.path.exists(appendFilePath):
        os.system(f"touch {appendFilePath}")
    flags = []
    with open(appendFilePath, encoding="utf-8", mode="r") as f:
        for line in f:
            item = json.loads(line)
            assert flag_key in item
            flags.append(item[flag_key])
    print(f"existed_flags: {flags}")
    data_to_run = []
    for i, item in enumerate(data):
        # write

        if flag_key not in item:
            item[flag_key] = i
        else:
            pass
        # print(item[flag_key])
        if item[flag_key] not in flags:
            print(item[flag_key])
            data_to_run.append(item)

    print(f"the total number of the data: {len(data)}......")
    print(f"the number of data to run: {len(data_to_run)}......")

    executor = conf.ThreadPoolExecutor(max_workers=max_workers)

    try:
        f = open(appendFilePath, encoding="utf-8", mode="a+")

        tasks = [executor.submit(run, item) for item in data_to_run]

        for it in conf.as_completed(tasks):
            if rt := it.result():
                print("##Question")
                print(rt["instruction"])
                print("##Conclusion")
                try:
                    print(rt["plain_text"])
                    print(rt["conclusion"])
                except:
                    pass
                f.write(json.dumps(rt, ensure_ascii=False) + "\n")
                f.flush()

    except Exception as e:
        print(f"Exception happens when in parallel...:{e}")
    finally:
        f.close()
        executor.shutdown(wait=True)


if __name__ == "__main__":
    data = []
    with open("data/open_instruction.jsonl", encoding="utf-8", mode="r") as f:
        for line in f:
            item = json.loads(line)
            data.append(item)
    # sampled_data = data[:1]
    os.makedirs("./results", exist_ok=True)
    run_concurrently(
        data,
        appendFilePath="results/open_instruction_results.jsonl",
        flag_key="instruction_id",
        max_workers=3,
    )
