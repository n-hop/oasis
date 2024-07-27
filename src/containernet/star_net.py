import logging
from topology import ITopology, MatrixType


class StarNet(ITopology):
    def __init__(self, yaml_description: str):
        """
        Args:
            some_parameter (int): An example parameter to initialize the class.
        """
        if not yaml_description:
            raise ValueError("yaml_description is empty.")
        self.top_config = self.load_yaml_config(yaml_description)
        self.adj_matrix = self.generate_adj_matrix(self.top_config.nodes)
        self.init_all_matrices()

    def get_matrix(self, mat_type: MatrixType):
        pass

    def init_all_matrices(self):
        pass

    def generate_adj_matrix(self, num_of_nodes: int):
        """
        Generate the adjacency matrix to describe a linear chain topology.
                only 0 and 1 are used to describe the link.
        Args:
            num_of_nodes (int): The number of nodes in the network.
                In a star chain topology, the number of nodes minus 1 is
                the number of child nodes.
        """
        hops = num_of_nodes - 1
        logging.info("Generate a %d-hops linear chain topology. %d",
                     hops, num_of_nodes)
        # Generate the adjacency matrix for the linear chain topology
        adj_matrix = [[0 for _ in range(num_of_nodes)]
                      for _ in range(num_of_nodes)]
        # TODO(.):
        logging.info("adj_matrix: %s", adj_matrix)
        return adj_matrix
