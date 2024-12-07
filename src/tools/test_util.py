import unittest
from .util import is_same_path
from .util import is_base_path
from .util import str_to_mbps
from .util import parse_test_file_name


class TestUtil(unittest.TestCase):

    def test_is_same_path_identical_paths(self):
        self.assertTrue(is_same_path(
            '/home/user/file.txt', '/home/user/file.txt'))

    def test_is_same_path_different_paths(self):
        self.assertFalse(is_same_path(
            '/home/user/file1.txt', '/home/user/file2.txt'))

    def test_is_same_path_with_double_slashes(self):
        self.assertTrue(is_same_path(
            '/home//user//file.txt', '/home/user/file.txt'))

    def test_is_same_path_with_trailing_slash(self):
        self.assertTrue(is_same_path(
            '/home/user/file.txt/', '/home/user/file.txt'))

    def test_is_same_path_with_mixed_slashes(self):
        self.assertTrue(is_same_path(
            '/home/user//file.txt/', '/home//user/file.txt'))

    def test_is_base_path_base_path(self):
        self.assertTrue(is_base_path(
            '/home/user', '/home/user/file.txt'))

    def test_is_base_path_not_base_path(self):
        self.assertFalse(is_base_path(
            '/home/user/docs', '/home/user/file.txt'))

    def test_is_base_path_identical_paths(self):
        self.assertTrue(is_base_path(
            '/home/user', '/home/user'))

    def test_is_base_path_with_double_slashes(self):
        self.assertTrue(is_base_path(
            '/home//user', '/home/user/file.txt'))

    def test_is_base_path_with_trailing_slash(self):
        self.assertTrue(is_base_path(
            '/home/user/', '/home/user/file.txt'))

    def test_is_base_path_with_mixed_slashes(self):
        self.assertTrue(is_base_path(
            '/home/user//', '/home//user/file.txt'))

    def test_str_to_mbps_kilobits(self):
        self.assertEqual(str_to_mbps(1000, "K"), 1.00)

    def test_str_to_mbps_megabits(self):
        self.assertEqual(str_to_mbps(1, "M"), 1.00)

    def test_str_to_mbps_gigabits(self):
        self.assertEqual(str_to_mbps(1, "G"), 1000.00)

    def test_str_to_mbps_no_unit(self):
        self.assertEqual(str_to_mbps(1000000, ""), 1.00)

    def test_str_to_mbps_invalid_unit(self):
        self.assertEqual(str_to_mbps(1000, "X"), 0.00)

    def test_parse_test_file_name_with_test_name(self):
        self.assertEqual(parse_test_file_name(
            'test.yaml:test1'), ('test.yaml', 'test1'))

    def test_parse_test_file_name_without_test_name(self):
        self.assertEqual(parse_test_file_name(
            'test.yaml'), ('test.yaml', None))

    def test_parse_test_file_name_with_multiple_colons(self):
        self.assertEqual(parse_test_file_name(
            'test.yaml:test1:test2'), (None, None))

    def test_parse_test_file_name_empty_string(self):
        self.assertEqual(parse_test_file_name(''), (None, None))

    def test_parse_test_file_name_only_colon(self):
        self.assertEqual(parse_test_file_name(':'), (None, None))


if __name__ == '__main__':
    unittest.main()
