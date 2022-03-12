from unittest import TestCase

from utils.string import split_number


class SplitNumberTest(TestCase):

    def test_split_number(self):
        self.assertEquals("123", split_number(123))
        self.assertEquals("1,234", split_number(1234))
        self.assertEquals("12,345", split_number(12345))
        self.assertEquals("123,000+", split_number(123456))
        self.assertEquals("1,234,000+", split_number(1234567))
