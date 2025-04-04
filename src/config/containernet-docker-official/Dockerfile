FROM containernet/containernet:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update
RUN python3 --version
RUN python3 -m pip install --upgrade pip
# Install tools needed for development
RUN python3 -m pip install PyYAML==6.0.1 psutil>=7.0.0 dataclasses>=0.6 matplotlib>=3.9.2
# -i https://pypi.tuna.tsinghua.edu.cn/simple

# override the entry point of containernet w/ absolute path to avoid
# path not found err when changing workdir
ENTRYPOINT [ "/containernet/util/docker/entrypoint.sh" ]

WORKDIR /root
