from unittest import TestCase

from models.video import get_bv


class TestVide(TestCase):
    def test_get_bv(self):
        self.assertEqual("BV1Ex411w7d2",
                         get_bv("https://bilibili.com/video/BV1Ex411w7d2/?spm_id_from"))

        self.assertEqual("BV1Ex411w7d2",
                         get_bv("https://bilibili.com/video/BV1Ex411w7d2"))

        self.assertEqual("BV1Ex411w7d2",
                         get_bv("BV1Ex411w7d2"))
