FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

# Install tools needed for development
# net-tools, iproute2 and python3 is neccessary for protocol run
RUN apt update && \
        apt upgrade --yes 

RUN apt-get install --yes \
        net-tools \
        iproute2 \
        python3 \
        libatomic1 \
        iperf3 \
        iputils-ping \
        python3-pip \
        iptables \
        curl \
        wget

RUN pip3 install \
        PyYAML==6.0.1 \
        matplotlib>=3.9.2

# install Perf tools for Azure
RUN apt-get install --yes \
        linux-tools-6.2.0-1016-azure \
        linux-cloud-tools-6.2.0-1016-azure \
        linux-tools-azure \
        linux-cloud-tools-azure


# Install go
RUN curl -L https://go.dev/dl/go1.23.0.linux-amd64.tar.gz | tar -C /usr/local -xz
ENV GOPATH=/go
ENV PATH=$PATH:/usr/local/go/bin:$GOPATH/bin

# Install go-gost to $GOPATH
RUN go install github.com/go-gost/gost/cmd/gost@latest

# Cleanup
RUN rm -rf /var/lib/apt/lists/*

# override the entry point of containernet w/ absolute path to avoid
# path not found err when changing workdir

WORKDIR /root
