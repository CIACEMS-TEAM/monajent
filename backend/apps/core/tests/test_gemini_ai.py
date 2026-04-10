"""Tests unitaires : parsing JSON sortie Gemini."""

from django.test import SimpleTestCase

from apps.core.services.gemini_ai import GeminiParseError, parse_model_json


class ParseModelJsonTests(SimpleTestCase):
    def test_plain_json(self):
        raw = '{"title": "Test", "price": 100000}'
        d = parse_model_json(raw)
        self.assertEqual(d['title'], 'Test')
        self.assertEqual(d['price'], 100000)

    def test_strips_markdown_fence(self):
        raw = '```json\n{"a": 1}\n```'
        d = parse_model_json(raw)
        self.assertEqual(d['a'], 1)

    def test_empty_raises(self):
        with self.assertRaises(GeminiParseError):
            parse_model_json('')

    def test_not_object_raises(self):
        with self.assertRaises(GeminiParseError):
            parse_model_json('[1,2]')
