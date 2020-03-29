import unittest
from app import app


class TestApp(unittest.TestCase):

    def test_update_data(self):
        app.update_data()


if __name__ == '__main__':
    unittest.main()