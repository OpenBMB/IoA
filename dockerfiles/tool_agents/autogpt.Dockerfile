FROM significantgravitas/auto-gpt:latest-dev

RUN echo "deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm main contrib non-free non-free-firmware \n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-updates main contrib non-free non-free-firmware \n\
deb https://mirrors.tuna.tsinghua.edu.cn/debian/ bookworm-backports main contrib non-free non-free-firmware \n\
deb https://security.debian.org/debian-security bookworm-security main contrib non-free non-free-firmware" | tee /etc/apt/sources.list
RUN cat /etc/apt/sources.list

RUN apt-get update --fix-missing && apt-get install -y \
chromium-driver firefox-esr \
ca-certificates \
libglib2.0-0 libnss3 libgconf-2-4 libfontconfig1

# Fix bugs in AutoGPT's docker
COPY im_client/agents/autogpt/autogpt_patch/web_selenium_latest_dev.py /app/autogpt/commands/web_selenium.py
COPY im_client/agents/autogpt/autogpt_patch/pyproject_latest_dev.toml /app/pyproject.toml