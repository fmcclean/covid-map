import unittest
import os
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestApp(unittest.TestCase):

    def setUp(self):
        from app import app
        self.app = app

    def test_update_data(self):
        self.app.update_data()


if __name__ == '__main__':
    unittest.main()