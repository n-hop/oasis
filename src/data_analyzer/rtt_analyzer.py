from .analyzer import IDataAnalyzer


class RTTAnalyzer(IDataAnalyzer):
    """Analyze and visualize multiple input rtt logs.
    """

    def analyze(self):
        return True

    def visualize(self):
        pass
