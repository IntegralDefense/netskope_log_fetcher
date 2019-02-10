""" This module defines the EventClient class which adds the following
to the inherited BaseNetskopeClient class: log types (self.type_list),
endpoint type (self.endpoint_type), and the URL endpoint used to pull
logs for Nestkope Events.
"""

import os

from netskope_fetcher.base import BaseNetskopeClient


class EventClient(BaseNetskopeClient):

    """ Holds information to be used when pulling down 'Event' logs.

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

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.type_list = ["page", "application", "audit", "infrastructure"]
        self.endpoint_type = "event"

        url = kwargs.get("url", None)

        self.url = url or (
            "https://{}.eu.goskope.com/api/v1/events"
            "".format(os.environ["NETSKOPE_TENANT_NAME"])
        )
