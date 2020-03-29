import unittest
import os


class TestApp(unittest.TestCase):
    def setUp(self):
        os.chdir('app')
        from app import app
        self.app = app

    def test_update_data(self):
        self.app.update_data()

if __name__ == '__main__':
    unittest.main()