import json
from urllib.parse import urlencode
import requests
from sanity import exceptions


def clean_params(params: dict):
    return {k: v for k, v in params.items() if v}


def merge_url(url: str, params: dict):
    if params and len(params) > 0:
        return url + "?" + urlencode(clean_params(params))
    return url


class ApiClient:
    def __init__(self, logger, base_uri, **kwargs):
        """
        :param logger: Logger
        :param base_uri: The base URI to the API
        """
        self.logger = logger
        self.base_uri = base_uri

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.session = requests.Session()

    @property
    def base_uri(self):
        return self._base_uri

    @base_uri.setter
    def base_uri(self, value):
        """The default base_uri"""
        if value and value.endswith("/"):
            value = value[:-1]
        self._base_uri = value

    def headers(self):
        if self.token:
            return {
                "Authorization": f"Bearer {self.token}"
            }
        return {}

    def request(self, method, url, data=None, params=None, content_type=None, load_json=True, parse_ndjson=False):
        if type(data) == dict:
            data = json.dumps(data)

        full_url = merge_url(self.base_uri + url, params)
        self.logger.info(full_url)

        h = self.headers()
        if content_type:
            h["Content-type"] = content_type

        result = self.session.request(
            method=method, url=full_url, data=data, headers=h
        )
        if result.status_code == 200 and load_json:
            return json.loads(result.text)
        elif result.status_code == 200 and parse_ndjson:
            results = []
            for ndjson_line in result.text.splitlines():
                if not ndjson_line.strip():
                    continue  # ignore empty lines
                json_line = json.loads(ndjson_line)
                results.append(json_line)
            return results
        else:
            self.logger.error(result.text)

        raise exceptions.SanityIOError
