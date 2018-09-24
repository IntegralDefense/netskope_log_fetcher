import os

from netskope_fetcher.base import BaseNetskopeClient


class AlertClient(BaseNetskopeClient):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_list = [
            "anomaly",
            "Compromised Credential",
            "policy",
            "Legal Hold",
            "malsite",
            "Malware",
            "DLP",
            "watchlist",
            "quarantine",
            "Remediation",
        ]
        self.endpoint_type = 'alert'

        if 'url' in kwargs:
            url = kwargs['url']
        else:
            url = None
        self.url = url or ("https://{}.eu.goskope.com/api/v1/alerts"
                           "".format(os.environ['NETSKOPE_TENANT_NAME']))
