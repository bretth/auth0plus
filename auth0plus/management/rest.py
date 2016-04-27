import json
import sys

import requests

from ..exceptions import Auth0Error
from ..settings import TIMEOUT


class RestClient(object):
    def __init__(self, jwt, telemetry=True, session=None):
        self.jwt = jwt
        self.requests = session or requests.Session()
        base_headers = {
            'Authorization': 'Bearer %s' % self.jwt,
            'Content-Type': 'application/json'
        }
        if telemetry:  # we don't want to pretend to be the official Auth0 client
            py_version = '%i.%i.%i' % (sys.version_info.major,
                                       sys.version_info.minor,
                                       sys.version_info.micro)

            base_headers['User-Agent'] = 'Python/%s' % py_version
        
        self.requests.headers.update(base_headers)

    def get(self, url, params={}, timeout=TIMEOUT):
        """
        :param str url: The url
        :param dict params:

        :return: list of dict responses
        :rtype: list
        """
        for kw, value in list(params.items()):
            if type(value) == bool:
                params[kw] = json.dumps(value)
            elif value is None:
                del params[kw]

        response = self.requests.get(
            url, params=params, headers={'Content-Type': None}, timeout=timeout)
        text = self._process_response(response)
        if not text:
            text = []
        elif not isinstance(text, list):
            text = [text]
        return text

    def post(self, url, data={}, timeout=TIMEOUT):
        response = self.requests.post(url, data=json.dumps(data), timeout=timeout)
        return self._process_response(response)

    def file_post(self, url, data={}, files={}, timeout=TIMEOUT):
        response = self.requests.post(
            url, data=data, files=files, headers={'Content-Type': None}, timeout=timeout)
        return self._process_response(response)

    def patch(self, url, data={}, timeout=TIMEOUT):
        response = self.requests.patch(url, data=json.dumps(data), timeout=timeout)
        return self._process_response(response)

    def delete(self, url, timeout=TIMEOUT):
        response = self.requests.delete(url, headers={'Content-Type': None}, timeout=timeout)
        return self._process_response(response)

    def _process_response(self, response):
        text = json.loads(response.text) if response.text else {}

        if isinstance(text, dict) and 'errorCode' in text:
            raise Auth0Error(status_code=text['statusCode'],
                             error_code=text['errorCode'],
                             message=text['message'])
 
        return text
