<h1 align="center"><img alt="Internet of Agents" src="https://github.com/OpenBMB/IoA/assets/32613237/04cbe3dc-84e1-4d70-ba5c-e8b07d3ee31d"  style="width: 1em; height: 1em;"> Internet of Agents</h1>

<p align="center">
    <a href="https://discord.gg/E5XPtynFDh">
        <img alt="Discord" src="https://img.shields.io/discord/1259737237763919963?logo=discord&style=flat&logoColor=white"/></a>
    <a href="https://github.com/astral-sh/ruff">
        <img alt="Code Formater: Ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json">
    </a>
    <a href="https://github.com/OpenBMB/IoA/LICENSE">
        <img alt="License" src="https://img.shields.io/github/license/OpenBMB/IoA">
    </a>
    <!-- <a href="https://openbmb.github.io/IoA/"><img src="https://img.shields.io/badge/Doc-En-white.svg" alt="EN doc"/></a>
    <a href="https://openbmb.github.io/IoA//doc_zh/index_zh.html"><img src="https://img.shields.io/badge/Doc-中文-white.svg" alt="ZH doc"/></a> -->
    <br>
    <br>【<a href="https://openbmb.github.io/IoA/">Documentation</a> | Paper (comming soon)</a>】<br>
</p>

---

## 🌎 What is Internet of Agents?

Imagine if AI agents could collaborate like humans do on the internet. That's the idea behind Internet of Agents (IoA)! It's an open-source framework that aims to create a platform where diverse AI agents can team up to tackle complex tasks. For example, agents like [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT) and [Open Interpreter](https://github.com/OpenInterpreter/open-interpreter) can come together, share their unique skills, and work on problems that might be too tricky for a single agent to solve.

## 🚀 Key Features

- 🌐 **Internet-Inspired Architecture**: Just like how the internet connects people, IoA can connect different AI agents across different environments.
- 🤝 **Autonomous Nested Team Formation**: Agents can form teams and sub-teams on their own, adapting to complex tasks.
- 🧩 **Heterogeneous Agent Integration**: Brings together agents with different skills and backgrounds, kind of like assembling an all-star team.
- ⏳ **Asynchronous Task Execution**: Agents can multitask, making the whole system more efficient.
- 🗣️ **Adaptive Conversation Flow**: The conversation flow is autonomously managed to keep agent conversations structured but flexible.
- 🔄 **Scalable and Extensible**: Easy to add new types of agents or tackle different kinds of tasks.

For more details, please refer to our paper.

<p align="center" style="color:RGB(160, 160, 160)">
    <img src="https://github.com/OpenBMB/IoA/assets/32613237/126082a8-432b-4039-8acd-49f4798a492c">
    A peek at IoA's layered architecture
</p>

<p align="center" style="color:RGB(160, 160, 160)">
    <img src="https://github.com/OpenBMB/IoA/assets/32613237/6d081cd8-a935-4e34-a24d-62eb65f8c6ec">
    How IoA works
</p>

---

## 🚀 Quick Start

Get IoA up and running in just a few steps:

### 1. 📋 Prerequisites
- Ensure you have [Docker](https://www.docker.com/) installed on your system.

### 2. 📥 Clone the Repository
```bash
git clone git@github.com:OpenBMB/IoA.git
cd IoA
```

### 3. 🏗️ Build Docker Images

#### Core Components
You can directly pull the pre-built docker images from docker hub
```bash
# Server
docker pull weize/ioa-server:latest

# Client
docker pull weize/ioa-client:latest

# Server Frontend
docker pull weize/ioa-server-frontend:latest

# Rename the images
docker tag weize/ioa-server:latest ioa-server:latest
docker tag weize/ioa-client:latest ioa-client:latest
docker tag weize/ioa-server-frontend:latest ioa-server-frontend:latest
```

<details>
<summary>Or you can build from source</summary>

```bash
# Server
docker build -f dockerfiles/server.Dockerfile -t ioa-server:latest .

# Client
docker build -f dockerfiles/client.Dockerfile -t ioa-client:latest .

# Server Frontend
docker build -f dockerfiles/server_frontend.Dockerfile -t ioa-server-frontend:latest .
```

</details>


#### Agent Images (Build as needed)

```bash
# ReAct Agent
docker pull weize/react-agent:latest
docker tag weize/react-agent:latest react-agent:latest

# AutoGPT (we have fixed some bugs in AutoGPT's original docker image)
docker pull weize/autogpt:latest
docker tag weize/autogpt:latest autogpt:latest

# Open Interpreter
docker pull weize/open-interpreter:latest
docker tag weize/open-interpreter:latest open-interpreter:latest
```

<details>
<summary>Or you can build from source</summary>

```bash
# ReAct Agent
docker build -f dockerfiles/tool_agents/react.Dockerfile -t react-agent:latest .

# AutoGPT (we have fixed some bugs in AutoGPT's original docker image)
docker build -f dockerfiles/tool_agents/autogpt.Dockerfile -t autogpt:latest .

# Open Interpreter
docker build -f dockerfiles/tool_agents/open_interpreter.Dockerfile -t open-interpreter:latest .
```

</details>


### 4. 🌐 Launch Milvus Service
```bash
docker network create agent_network
docker-compose -f dockerfiles/compose/milvus.yaml up
```

### 5. 🎬 Start IoA
```bash
cd dockerfiles/compose/
cp .env_template .env
```

In `.env`, fill in your OpenAI API key and other optional environment variables. Then for a quick demo with AutoGPT and Open Interpreter:
```bash
cd ../../
docker-compose -f dockerfiles/compose/open_instruction.yaml up
```

And you will set up your own small-scale Internet of Agents with AutoGPT and Open Interpreter!

### 6. 🧪 Test It Out
You can use the following script to test IoA on our Open Instruction dataset.
```bash
python scripts/open_instruction/test_open_instruction.py
```

Or simply send a post request like:
```python
import requests

goal = "I want to know the annual revenue of Microsoft from 2014 to 2020. Please generate a figure in text format showing the trend of the annual revenue, and give me a analysis report."

response = requests.post(
    "http://127.0.0.1:5050/launch_goal",
    json={
        "goal": goal,
        "max_turns": 20,
        "team_member_names": ["AutoGPT", "Open Interpreter"],   # When it is left "None", the agent will decide whether to form a team autonomously
    },
)

print(response)
```

<details>
<summary>🤔 Want to run IoA across different devices?</summary>

Check out our [distributed setup guide](https://asl-r.github.io/distributed_service/config.html). 
We're continuously improving our documentation, so your feedback is valuable!
</details>

---

# 🌟 Join the IoA Adventure!

We're just getting started with IoA, and we'd love your help to make it even better! Got ideas for cool ways to use IoA, like connecting PC agents with mobile agents? We're all ears!

- 👾 Chat with us on [Discord](https://discord.gg/E5XPtynFDh)
- ✉️ Drop us a line at ioa.thunlp@gmail.com

Let's build the future of AI collaboration together! 🚀


