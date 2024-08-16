# import logging
from .default_protocol import DefaultProtocol


class TCPProtocol(DefaultProtocol):
    def get_protocol_name(self) -> str:
        return "tcp"