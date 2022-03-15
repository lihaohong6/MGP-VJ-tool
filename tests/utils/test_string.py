import unittest
from unittest import TestCase

from utils.string import process_lyrics_jap


class Test(TestCase):
    def test_auto_lj(self):
        pass

    s1 = """翼広げ、どこか遠く、

ひとりという名の鳥になり飛んで

いけたらいいな、そこには見たことない

きれいなものがあるの"""

    more_newline = "\n\n\n\n\n\n".join(["ABC\n\n\nDEF\n\n\n\nGHI\n\n\n\nJKL" for _ in range(3)])
    more_newline_expected = "\n\n".join(["ABC\nDEF\nGHI\nJKL" for _ in range(3)])

    def test_process_lyrics_jap(self):
        self.assertEqual("\n".join(self.s1.split("\n\n")),
                         process_lyrics_jap(self.s1))
        self.assertEqual(self.more_newline_expected, process_lyrics_jap(self.more_newline))


if __name__ == "__main__":
    unittest.main()

