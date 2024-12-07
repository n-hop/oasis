import unittest
from unittest.mock import patch
import yaml
from src.core.config import load_all_tests
from src.core.config import Test, TopologyConfig
from src.core.topology import TopologyType


class TestLoadAllTests(unittest.TestCase):

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_all_tests_with_valid_yaml(self, mock_yaml_load, mock_open):
        # Mock data
        mock_yaml_content = {
            "tests": {
                "test1": {
                    "if": True,
                    # other test configurations
                },
                "test2": {
                    "if": False,
                    # other test configurations
                },
                "test3": {
                    # 'if' key not present, should default to True
                    # other test configurations
                }
            }
        }
        mock_yaml_load.return_value = mock_yaml_content

        test_yaml_file = 'test.yaml'
        test_name = 'all'

        # Call the function
        result = load_all_tests(test_yaml_file, test_name)

        # Check that open was called
        mock_open.assert_called_once_with(
            test_yaml_file, 'r', encoding='utf-8')

        # Verify the result
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].name, 'test1')
        self.assertEqual(result[1].name, 'test3')

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_all_tests_with_specific_test_name(self, mock_yaml_load, mock_open):
        # Mock data
        mock_yaml_content = {
            "tests": {
                "test1": {
                    "if": True,
                },
                "test2": {
                    "if": True,
                }
            }
        }
        mock_yaml_load.return_value = mock_yaml_content

        test_yaml_file = 'test.yaml'
        test_name = 'test1'

        # Call the function
        result = load_all_tests(test_yaml_file, test_name)

        # Verify the result
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].name, 'test1')

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_load_all_tests_file_not_found(self, mock_open):
        test_yaml_file = 'non_existing.yaml'
        result = load_all_tests(test_yaml_file)

        # Verify the result is empty due to file not found
        self.assertEqual(result, [])

    @patch('builtins.open')
    @patch('yaml.safe_load', side_effect=yaml.YAMLError)
    def test_load_all_tests_yaml_error(self, mock_yaml_load, mock_open):
        test_yaml_file = 'invalid.yaml'
        result = load_all_tests(test_yaml_file)

        # Verify the result is empty due to YAML error
        self.assertEqual(result, [])

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_all_tests_no_tests_key(self, mock_yaml_load, mock_open):
        # Mock data without 'tests' key
        mock_yaml_content = {}
        mock_yaml_load.return_value = mock_yaml_content

        test_yaml_file = 'test.yaml'
        result = load_all_tests(test_yaml_file)

        # Verify the result is empty
        self.assertEqual(result, [])

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_all_tests_no_active_tests(self, mock_yaml_load, mock_open):
        # Mock data with all tests inactive
        mock_yaml_content = {
            "tests": {
                "test1": {
                    "if": False,
                },
                "test2": {
                    "if": False,
                }
            }
        }
        mock_yaml_load.return_value = mock_yaml_content

        test_yaml_file = 'test.yaml'
        result = load_all_tests(test_yaml_file)

        # Verify the result is empty
        self.assertEqual(len(result), 0)


class TestTestClass(unittest.TestCase):

    def setUp(self):
        self.test_yaml_active = {
            "if": True,
            "topology": {
                "topology_type": "linear",
                "name": "test_topology"
            }
        }
        self.test_yaml_inactive = {
            "if": False,
            "topology": {
                "topology_type": "linear",
                "name": "test_topology"
            }
        }
        self.test_yaml_no_if = {
            "topology": {
                "topology_type": "linear",
                "name": "test_topology"
            }
        }
        self.test_yaml_no_topology = {
            "if": True
        }

    def test_yaml_method(self):
        test_instance = Test(self.test_yaml_active, "test1")
        self.assertEqual(test_instance.yaml(), self.test_yaml_active)

    def test_is_active(self):
        test_instance_active = Test(self.test_yaml_active, "test1")
        test_instance_inactive = Test(self.test_yaml_inactive, "test2")
        test_instance_no_if = Test(self.test_yaml_no_if, "test3")
        test_instance_none = Test({}, "test4")

        self.assertTrue(test_instance_active.is_active())
        self.assertFalse(test_instance_inactive.is_active())
        self.assertTrue(test_instance_no_if.is_active())
        self.assertFalse(test_instance_none.is_active())

    @patch('src.core.config.IConfig.load_yaml_config')
    def test_load_topology(self, mock_load_yaml_config):
        mock_load_yaml_config.return_value = TopologyConfig(
            topology_type=TopologyType.linear, name="test_topology", nodes=5)

        test_instance = Test(self.test_yaml_active, "test1")
        result = test_instance.load_topology("/fake/path")
        # no 'topology' in file
        self.assertIsNone(result)
        mock_load_yaml_config.assert_called_once_with(
            "/fake/path", self.test_yaml_active["topology"], 'topology')

    @patch('src.core.config.IConfig.load_yaml_config')
    def test_load_topology_no_topology(self, mock_load_yaml_config):
        test_instance = Test(self.test_yaml_no_topology, "test1")
        result = test_instance.load_topology("/fake/path")

        self.assertIsNone(result)
        mock_load_yaml_config.assert_not_called()

    @patch('src.core.config.IConfig.load_yaml_config')
    def test_load_topology_invalid_topology(self, mock_load_yaml_config):
        mock_load_yaml_config.return_value = None

        test_instance = Test(self.test_yaml_active, "test1")
        result = test_instance.load_topology("/fake/path")

        self.assertIsNone(result)
        mock_load_yaml_config.assert_called_once_with(
            "/fake/path", self.test_yaml_active["topology"], 'topology')

    @patch('src.core.config.IConfig.load_yaml_config')
    def test_load_topology_unsupported_type(self, mock_load_yaml_config):
        mock_load_yaml_config.return_value = TopologyConfig(
            topology_type=TopologyType.butterfly, name="test_topology", nodes=5)

        test_instance = Test(self.test_yaml_active, "test1")
        result = test_instance.load_topology("/fake/path")

        self.assertIsNone(result)
        mock_load_yaml_config.assert_called_once_with(
            "/fake/path", self.test_yaml_active["topology"], 'topology')


if __name__ == '__main__':
    unittest.main()
