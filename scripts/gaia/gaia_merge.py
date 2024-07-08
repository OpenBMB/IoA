import os
import json
import re

ans_pat = re.compile(r"(FINAL ANSWER|EDUCATED GUESS): (.*)")
all_results = []

for level in ["level1", "level2", "level3"]:
    result_dir = f"results/gaia/{level}/processed"
    acc = 0
    total = 0
    for file in os.listdir(result_dir):
        if not file.endswith(".json"):
            continue
        total += 1
        with open(os.path.join(result_dir, file), "r") as f:
            data = json.load(f)
        task_id = file.split(".")[0]
        model_answer = ans_pat.findall(data[-1])[0][1]
        all_results.append({"task_id": task_id, "model_answer": model_answer})
        if model_answer.strip().lower() == data[-2].lower():
            acc += 1
        else:
            pass
    print(f"Level {level} accuracy: {acc / total}")

with open("results/gaia/gaia_merged.jsonl", "w") as f:
    f.writelines([json.dumps(result, ensure_ascii=False) + "\n" for result in all_results])
