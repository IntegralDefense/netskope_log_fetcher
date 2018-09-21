import os

from netskope_fetcher.base import BaseNetskopeClient


class EventClient(BaseNetskopeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_list = ['page', 'application', 'audit', 'infrastructure']

        if 'url' in kwargs:
            url = kwargs['url']
        else:
            url = None
        self.url = url or (
            "https://{}.goskope.com/api/v1/events"
            "".format(os.environ['NETSKOPE_TENANT_NAME']))
        print(self.url)