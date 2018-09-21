from datetime import datetime
from multiprocessing import Pool, cpu_count
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
            p.map(self._get_all_event_type_worker, self.type_list)

    def _get_all_event_type_worker(self, event_type):
        params = {
            'token': self.token.auth_token,
            'type': event_type,
            'starttime': self.start,
            'endtime': self.end,
        }
        self.log_dictionary[event_type] = self._call_api(params)

    def _call_api(self, _params):
        r = requests.get(url=self.url, params=_params)
        if r.status_code is not 200:
            # Log the issue / raise exception
            pass
        if r.json()['status'] is not 'success':
            # Log the issue / rasie exception
            pass
        return r.json()['data']

    def get_all_event_types(self):
        self._get_all_event_types_foreman()
