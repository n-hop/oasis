import logging
import os
from .analyzer import IDataAnalyzer


class ScpAnalyzer(IDataAnalyzer):
    """Analyze and visualize multiple input scp logs.
    """

    def analyze(self):
        for input_log in self.config.input:
            logging.info(f"Analyze scp log: %s", input_log)
            if not os.path.exists(input_log):
                logging.info("The scp log file %s does not exist", input_log)
                return False
            with open(input_log, "r", encoding="utf-8") as f:
                lines = f.readlines()
                has_passed = any("passed" in line for line in lines)
                has_percent = any("100%" in line for line in lines)
                has_script_done = any("Script done." in line for line in lines)
                if not has_percent or not has_script_done or not has_passed:
                    logging.info(
                        "The scp log %s does not contain the expected content", input_log)
                    return False
            logging.info("The scp log %s check is passed", input_log)
        return True

    def visualize(self):
        pass
