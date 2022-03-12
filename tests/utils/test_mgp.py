import asyncio
from unittest import TestCase

from models.creators import Person
from utils.mgp import producer_template_exists, get_producer_templates


class TestProducerTemplate(TestCase):
    def test_template_exists(self):
        true = ["Wowaka", "针原翼"]
        for t in true:
            self.assertTrue(producer_template_exists(t))
            # print("Template " + t + " exists.")
        false = ["黑幕", "这是一个不存在的模板"]
        for t in false:
            self.assertFalse(producer_template_exists(t))
            # print("Template " + t + " does not exist.")

    def test_get_producer_templates(self):
        producers = [Person("WowakaP", ["黑幕"]),
                     Person("谁也不是", ["胡话P", "LyricsKai"]),
                     Person("什么鬼", ["HarryP", "针原翼"])]
        self.assertEquals(['Wowaka', 'HarryP'], asyncio.run(get_producer_templates(producers)))
