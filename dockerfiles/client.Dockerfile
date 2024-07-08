# start with a python:3.10 image
FROM python:3.10.13-slim

# Mark the role played by this container as ReAct Agent
EXPOSE 5050

# Set the working directory in the container
WORKDIR /app

COPY im_client/requirements.txt /app/requirements.txt
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into container at /app
COPY ./im_client /app
COPY ./common /app/common

# Set the entry point for running the test_react_agent python file
ENTRYPOINT [ "python", "main.py" ]

