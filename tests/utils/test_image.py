from unittest import TestCase

from utils.image import remove_black_boarders, pick_color, Color, text_color


class ImageTest(TestCase):
    def test_remove_black_boarders(self):
        pass
        # remove_black_boarders("output/temp.jpeg", "output/Booo!封面.jpeg")

    def test_pick_color(self):
        pass
        # print(pick_color("output/Booo!封面.jpeg"))

    def test_text_color(self):
        black = Color(0, 0, 0)
        white = Color(255, 255, 255)
        self.assertEqual(white, text_color(Color(100, 100, 150)))
        self.assertEqual(white, text_color(black))
        self.assertEqual(black, text_color(white))
        self.assertEqual(black, text_color(Color(130, 140, 150)))
        self.assertEqual(black, text_color(Color(0, 255, 255)))
