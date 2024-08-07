FROM containernet/containernet:latest

ARG DEBIAN_FRONTEND=noninteractive

RUN pip3 install PyYAML==6.0.2

# override the entry point of containernet w/ absolute path to avoid
# path not found err when changing workdir
ENTRYPOINT [ "/containernet/util/docker/entrypoint.sh" ]

WORKDIR /root
