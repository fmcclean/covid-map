import unittest
import os
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


class TestApp(unittest.TestCase):

    def setUp(self):
        from app import app
        self.app = app
        self.app.update_data()

    def test_create_choropleth(self):
        self.app.create_figure('choropleth')

    def test_create_density(self):
        self.app.create_figure('density')


if __name__ == '__main__':
    unittest.main()
