from datetime import datetime
import os

import requests


def validate_limit(limit):
    if limit > 4999:
        limit = 4999
    return limit


class BaseNetskopeClient:

    def __init__(self, token, start=None, end=None, limit=None, skip=None, url=None):
        self.token = token
        self.end = end or int(datetime.now().timestamp())
        self.start = start or (
            self.end - int(os.environ['NETSKOPE_DEFAULT_INTERVAL']))
        self.limit = validate_limit(limit)
        self.skip = skip
        self.type_list = []
        self.url = url


class EventClient(BaseNetskopeClient):

    def __init__(self, token, start=None, end=None, limit=None, skip=None, url=None):
        super().__init__(token, start, end, limit, skip)
        self.type_list = ['page', 'application', 'audit', 'infrastructure']
        self.url = url or ("https://{}/goskope.com/api/v1/events"
                           "".format(os.environ['NETSKOPE_TENANT_NAME']))

    def all_events_generator(self):
        for _type in self.type_list:
            logs = self.get_event(_type)
            yield logs

    def log_generator(self, log_list):

    def get_event(self, event_type):
        params = {
            'type': event_type,
            'starttime': self.start,
            'endtime': self.end,
        }
        if self.limit:
            params['limit'] = self.limit
        if self.skip:
            params['skip'] = self.skip  
        log_list
        for _type in self.type_list:
            logs = self.get_event(_type)
            log_list.append(logs)
        return log_list

    def 

            # Call api for events for specific type