# start with a python:3.10 image
FROM python:3.10.13-slim

# RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware \n\
# deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware \n\
# deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware \n\
# deb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" | tee /etc/apt/sources.list

EXPOSE 7070

# Set the working directory in the container
WORKDIR /app

# Copy the requirements.txt into container at /app
COPY im_client/agents/open_interpreter/requirements.txt .

RUN apt-get update && apt-get install -y gcc \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Intall the project dependencies dynamically
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple \
    && pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into container at /app
COPY im_client/agents/open_interpreter .

# Set the entry point for running the test_react_agent python file
ENTRYPOINT [ "python", "open_interpreter_agent.py" ]

