import os

from netskope_fetcher.base import BaseNetskopeClient


class AlertClient(BaseNetskopeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_list = [
            'anomaly',
            'Compromised Credential',
            'policy',
            'Legal Hold',
            'malsite',
            'Malware',
            'DLP',
            'watchlist',
            'quarantine',
            'Remediation',
        ]

        if 'url' in kwargs:
            url = kwargs['url']
        else:
            url = None
        self.url = url or ("https://{}.goskope.com/api/v1/alerts"
                           "".format(os.environ['NETSKOPE_TENANT_NAME']))
        print(self.url)
