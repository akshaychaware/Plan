import re

from rest_framework.parsers import JSONParser
from rest_framework.renderers import JSONRenderer


def _to_camel(key):
    head, *tail = key.split('_')
    return head + ''.join(part.title() for part in tail)


def _to_snake(key):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', key).lower()


def convert_keys(data, convert):
    if isinstance(data, dict):
        return {convert(k) if isinstance(k, str) else k: convert_keys(v, convert) for k, v in data.items()}
    if isinstance(data, (list, tuple)):
        return [convert_keys(item, convert) for item in data]
    return data


class CamelCaseJSONRenderer(JSONRenderer):
    def render(self, data, accepted_media_type=None, renderer_context=None):
        return super().render(convert_keys(data, _to_camel), accepted_media_type, renderer_context)


class CamelCaseJSONParser(JSONParser):
    def parse(self, stream, media_type=None, parser_context=None):
        return convert_keys(super().parse(stream, media_type, parser_context), _to_snake)
