import unittest
from typing import Callable
from unittest import TestCase

from utils.japanese import is_hiragana, is_katakana, is_kana, is_kanji, furigana_local

hiragana = "あいうえおをだってん"
katakana = "アイウエオダッテン"
kanji = "々我你他心踊重甜笺繰"


class Test(TestCase):
    def test(self, func: Callable[[str], bool] = None,
             true: str = "", false: str = ""):
        for c in true:
            self.assertTrue(func(c))
        for c in false:
            self.assertFalse(func(c))

    def test_is_hiragana(self):
        self.test(is_hiragana, hiragana, kanji + katakana)

    def test_is_katakana(self):
        self.test(is_katakana, katakana, kanji + hiragana)

    def test_is_kana(self):
        self.test(is_kana, hiragana + katakana, kanji)

    def test_is_kanji(self):
        self.test(is_kanji, kanji, hiragana + katakana)

    def test_furigana_local(self):
        original = "接木（つぎき）のような時制の不連続。広場に殺（し）した感嘆符の葬列。"
        expected = "{{photrans|接木|つぎき}}のような時制の不連続。広場に{{photrans|殺|し}}した感嘆符の葬列。"
        self.assertEqual(expected, furigana_local(original))
        original = "水底に沈(しず)く彫刻の太()陽。"
        expected = "水底に{{photrans|沈|しず}}く彫刻の太()陽。"
        self.assertEqual(expected, furigana_local(original))
        original = "水底に沈(测试)く彫刻の（の）太陽。"
        self.assertEqual(original, furigana_local(original))


if __name__ == "__main__":
    unittest.main()
