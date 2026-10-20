FROM open-interpreter:deps
WORKDIR /app
COPY im_client/agents/open_interpreter/ /app/
ENTRYPOINT ["python", "open_interpreter_agent.py"]
