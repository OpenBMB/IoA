# start with a python:3.10 image
FROM python:3.10.13-slim

# Mark the role played by this container as ReAct Agent
EXPOSE 7788

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into container at /app
COPY ./im_server/requirements.txt ./
RUN pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple && pip install --no-cache-dir -r requirements.txt
COPY ./im_server ./
COPY ./common ./common

# Set the entry point for running the test_react_agent python file
ENTRYPOINT [ "python", "app.py" ]
# ENTRYPOINT [ "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:7788", "app:app" ]
