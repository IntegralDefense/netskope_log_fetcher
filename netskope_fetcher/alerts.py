import os

from netskope_fetcher.base import BaseNetskopeClient


class AlertClient(BaseNetskopeClient):

    """ Holds information to be used when pulling down 'Alert' logs.

    Inherits
    ----------
    BaseNetskopeClient

    Attributes
    ----------
    type_list: list
        The various types of logs that can be pulled down from Netskope
        according to Netskope documentation.
        https://valvoline.eu.goskope.com/docs/Netskope_Help/en/
        rest-api/http-endpoints.html
    endpoint_type: str
        The netskope rest endpoint that this object relates to.
    url: str
        The URL of the endpoint
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type_list = [
            "anomaly",
            "Compromised Credential",
            "policy",
            # "Legal Hold",    THROWS ERRORS AS INVALID
            "malsite",
            "Malware",
            "DLP",
            "watchlist",
            "quarantine",
            # "Remediation",   THROWS ERRORS AS INVALID
        ]
        self.endpoint_type = 'alert'

        if 'url' in kwargs:
            url = kwargs['url']
        else:
            url = None
        self.url = url or ("https://{}.eu.goskope.com/api/v1/alerts"
                           "".format(os.environ['NETSKOPE_TENANT_NAME']))
