from datetime import datetime
from multiprocessing import Pool, cpu_count
import logging
import json
import os

import requests


class BaseNetskopeClient:

    def __init__(self, token=None, start=None, end=None, url=None):
        self.token = token
        self.end = end or int(datetime.now().timestamp())
        self.start = start or (
            self.end - int(os.environ['NETSKOPE_DEFAULT_INTERVAL']))
        self.type_list = []
        self.log_dictionary = {}
        self.url = url

    def _get_all_event_types_foreman(self):
        cpus = cpu_count()
        with Pool(processes=cpus) as p:
            map_logs_list = p.map(
                self._get_all_event_type_worker,
                self.type_list
            )
            self.log_dictionary = {logs[0]: logs[1] for logs in map_logs_list}

    def _get_all_event_type_worker(self, event_type):
        params = {
            'token': self.token.auth_token,
            'type': event_type,
            'starttime': self.start,
            'endtime': self.end,
        }
        return (event_type, self._call_api(params))

    def _call_api(self, _params):
        r = requests.get(url=self.url, params=_params)
        if (r.status_code != 200) or (r.json()['status'] != 'success'):
            # Log the issue / raise exception
            logging.error(f'Response received from requests: '
                          f'{json.dumps(r.json(), indent=2)}')
            return []
        try:
            return r.json()['data']
        except KeyError as k:
            # No data, return empty list
            return []

    def get_all_event_types(self):
        self._get_all_event_types_foreman()
