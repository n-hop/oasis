from enum import IntEnum


class MatrixType(IntEnum):
    # Adjacency matrix to describe the network topology
    ADJACENCY_MATRIX = 0,
    # Bandwidth matrix to describe the network bandwidth link-by-link
    BANDWIDTH_MATRIX = 1,
    # Loss matrix to describe the network loss link-by-link
    LOSS_MATRIX = 2,
    # Latency matrix to describe the network latency link-by-link
    LATENCY_MATRIX = 3,
    # Jitter matrix to describe the network jitter link-by-link
    JITTER_MATRIX = 4,
