# Adapted from AutoGen https://github.com/microsoft/autogen/tree/gaia_multiagent_v01_march_1st/samples/tools/autogenbench/scenarios/GAIA/Templates/Orchestrator

import sys
import os
import json
import openai
import copy

sys.path.append(".")
sys.path.append("../")
from common.utils.database_utils import AutoStoredDict

from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("--db_path", type=str)
parser.add_argument("--level", type=int, choices=[1, 2, 3])
args = parser.parse_args()

client = openai.OpenAI()

tasks = AutoStoredDict(
    args.db_path,
    tablename="chat",
).todict()

STARTING_PROMPT = """Earlier you were asked the following:

{}

Your team then worked diligently to address that request. Here is a transcript of that conversation:"""


END_PROMPT = """Read the above conversation and output a FINAL ANSWER to the question. The question is repeated here for convenience:

{}

To output the final answer, use the following template: FINAL ANSWER: [YOUR FINAL ANSWER]
Your FINAL ANSWER should be a number OR as few words as possible OR a comma separated list of numbers and/or strings.
ADDITIONALLY, your FINAL ANSWER MUST adhere to any formatting instructions specified in the original question (e.g., alphabetization, sequencing, units, rounding, decimal places, etc.)
If you are asked for a number, express it numerically (i.e., with digits rather than words), don't use commas, and don't include units such as $ or percent signs unless specified otherwise.
If you are asked for a string, don't use articles or abbreviations (e.g. for cities), unless specified otherwise. Don't output any final sentence punctuation such as '.', '!', or '?'.
If you are asked for a comma separated list, apply the above rules depending on whether the elements are numbers or strings.
If you are unable to determine the final answer, output 'FINAL ANSWER: Unable to determine'"""

GUESS_PROMPT = """I understand that a definitive answer could not be determined. Please make a well-informed EDUCATED GUESS based on the conversation.

To output the educated guess, use the following template: EDUCATED GUESS: [YOUR EDUCATED GUESS]
Your EDUCATED GUESS should be a number OR as few words as possible OR a comma separated list of numbers and/or strings. DO NOT OUTPUT 'I don't know', 'Unable to determine', etc.
ADDITIONALLY, your EDUCATED GUESS MUST adhere to any formatting instructions specified in the original question (e.g., alphabetization, sequencing, units, rounding, decimal places, etc.)
If you are asked for a number, express it numerically (i.e., with digits rather than words), don't use commas, and don't include units such as $ or percent signs unless specified otherwise.
If you are asked for a string, don't use articles or abbreviations (e.g. for cities), unless specified otherwise. Don't output any final sentence punctuation such as '.', '!', or '?'.
If you are asked for a comma separated list, apply the above rules depending on whether the elements are numbers or strings."""

result_dir = f"results/gaia/level{args.level}"
os.makedirs(os.path.join(result_dir, "processed"), exist_ok=True)


def handle_unable_to_determine(messages, extracted_text):
    messages = copy.deepcopy(messages)
    messages += [{"role": "assistant", "content": extracted_text}, {"role": "user", "content": GUESS_PROMPT}]
    response = client.chat.completions.create(messages=messages, model="gpt-4o", temperature=0)
    extracted_text = response.choices[0].message.content
    return extracted_text


for root, dirs, files in os.walk(result_dir):
    for file in files:
        if os.path.exists(os.path.join(result_dir, "processed", file)):
            continue
        if not file.endswith(".json"):
            continue
        with open(os.path.join(root, file), "r") as f:
            data = json.load(f)
        try:
            comm_id, conclusion, result = data
            goal = tasks[comm_id]["chat_record"][0].goal
            chat_record = tasks[comm_id]["chat_record"]
        except Exception as e:
            print(e)
            continue

        messages = (
            [{"role": "user", "content": STARTING_PROMPT.format(goal)}]
            + [{"role": "assistant", "content": f"[{item.sender}]: {item.content}"} for item in chat_record]
            + [{"role": "user", "content": END_PROMPT.format(goal)}]
        )

        response = client.chat.completions.create(messages=messages, model="gpt-4o", temperature=0)
        extracted_text = response.choices[0].message.content
        print(extracted_text)
        if "Unable to determine".lower() in extracted_text.lower():
            extracted_text = handle_unable_to_determine(messages, extracted_text)
            print(extracted_text)
        with open(os.path.join(result_dir, "processed", file), "w") as f:
            json.dump([comm_id, conclusion, result, extracted_text], f, indent=2, ensure_ascii=False)
