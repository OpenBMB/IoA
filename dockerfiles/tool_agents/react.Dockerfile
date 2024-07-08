# start with a python:3.10 image
FROM python:3.10.13-slim

EXPOSE 7070

# Set the working directory in the container
WORKDIR /app

# RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware \n\
# deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware \n\
# deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware \n\
# deb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" > /etc/apt/sources.list

# Copy the requirements.txt into container at /app
COPY im_client/agents/react/requirements.txt .

RUN apt-get update \
    && apt-get install --no-install-recommends -y git \
    && pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt \
    && playwright install --with-deps chromium \
    && apt-get autoremove -y git \
    && rm -rf /var/lib/apt/lists/*

COPY im_client/agents/react /app
COPY im_client/agents/tools /app/tools
COPY common /app/common
COPY im_client/llms /app/llms
COPY im_client/memory /app/memory
COPY im_client/prompts /app/prompts

# Set the entry point for running the test_react_agent python file
ENTRYPOINT [ "python", "react_agent.py" ]
