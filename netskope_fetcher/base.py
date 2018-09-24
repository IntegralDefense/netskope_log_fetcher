from datetime import datetime
from multiprocessing import Pool, cpu_count
import logging
import json
import os

import requests


class BaseNetskopeClient:

    """ Base class for Netskope clients.

    Attributes
    ----------
    token: netskope_fetcher.token.Token object
        Holds the token information used for authentication and
        authorization in the API calls.
    end: int
        The end time in epoch format for this run of the program
    start: int
        The start time in epoch format for this run of the program
    type_list: list
        ***WILL BE OVERRIDDEN BY CHILD CLASS***
        The various types of logs that can be pulled down from Netskope
        according to Netskope documentation.
        https://valvoline.eu.goskope.com/docs/Netskope_Help/en/
        rest-api/http-endpoints.html
    log_dictionary: dict
        Dictonary with log types as keys and list of logs as values.
        Ex:
        {
            'application': [{log1}, {log2}, ...],
            'page': [{log1}, {log2}, ...],
        }
    url: str
    ***WILL BE OVERRIDDEN BY CHILD CLASS***
        The URL of the endpoint
    """

    def __init__(self, token=None, start=None, end=None, url=None):
        self.token = token
        self.end = end or int(datetime.now().timestamp())
        self.start = start or (
            self.end - int(os.environ['NETSKOPE_DEFAULT_INTERVAL']))
        self.type_list = []
        self.log_dictionary = {}
        self.url = url

    def _get_all_event_types_foreman(self):
        """ Controls multiprocessing pool so that the logs can be pulled
            down in parallel instead of sequentially.

            The Foreman sets up the multiprocessing pool and puts
            the processes to work. He then appends the logs to
            log_dictionary.
        """

        cpus = cpu_count()
        with Pool(processes=cpus) as p:
            map_logs_list = p.map(
                self._get_all_event_type_worker,
                self.type_list
            )
            self.log_dictionary = {logs[0]: logs[1] for logs in map_logs_list}

    def _get_all_event_type_worker(self, event_type):
        """ Setups up the request parameters and calls the API
            communication function.

        Parameters
        ----------
        event_type: str
            The type of event. For example:  'application' or 'page'    
        
        Returns
        ----------
        tuple: (The type of event, the list of logs for the event)
        """

        params = {
            'token': self.token.auth_token,
            'type': event_type,
            'starttime': self.start,
            'endtime': self.end,
        }
        return (event_type, self._call_api(params))

    def _call_api(self, _params):
        """ Pulls down logs from the Netskope API endpoint.

            Uses the 'requests' module to pull down logs.

        Returns
        ----------
        A list:
            List will be empty if there was an error and will return
            a list of dict-formatted logs if there were logs available.
        """

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
        """ Calls helper function to handle multiprocessing."""
        
        self._get_all_event_types_foreman()
