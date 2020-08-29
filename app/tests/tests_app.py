import unittest
import os
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestApp(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        from app import app
        self.app = app

    def test_create_figure(self):
        self.app.create_figure()


if __name__ == '__main__':
    unittest.main()
