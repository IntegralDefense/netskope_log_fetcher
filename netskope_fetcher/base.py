from datetime import datetime
import asyncio
import logging
import json
import os


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
    session: aiohttp.ClientSession object
        Used for non-blocking HTTP requests
    """

    def __init__(self, token=None, start=None,
                 end=None, url=None, session=None):
        self.token = token
        self.end = end or int(datetime.now().timestamp())
        self.start = start or (
            self.end - int(os.environ['NETSKOPE_DEFAULT_INTERVAL']))
        self.type_list = []
        self.log_dictionary = {}
        self.url = url
        self.session = session
        self.max_logs = 5000

    async def get_logs(self, session, loop):
        """ This function serves as the entry point into the
            async functions of this class.

            Awaits the HTTP requests and log gathering that is processed
            concurrently for each log type.
        """

        await self._async_foreman(session, loop)

    async def _async_foreman(self, session, loop):
        """ Creates a task for each log type to be pulled down (since
            each type will be a separate API call) and then adds them
            to the event loop.

        Parameters
        ----------
        session: aiohttp.ClientSession object
            Used for non-blocking HTTP requests
        loop: asyncio.AbstractEventLoop
            The current running loop in which we want to add tasks to
        """

        tasks = [
            self._async_worker(session, type_) for type_ in self.type_list
        ]
        await asyncio.gather(*tasks, loop=loop)

    async def _async_worker(self, session, event_type):
        """ Setups up the request parameters and calls the API
            communication function.

        Parameters
        ----------
        session: aiohttp.ClientSession object
            Used for non-blocking HTTP requests
        event_type: str
            The type of event. For example:  'application' or 'page'
        """

        params = {
            'token': self.token.auth_token,
            'type': event_type,
            'starttime': self.start,
            'endtime': self.end,
        }
        await self._api_call_2(session, params)

    async def _api_call_2(self, session, _params, pagination=0, skip=0):
        """ Pulls down logs from the Netskope API endpoint.

            Uses non-blocking HTTP requests to pull down the logs from
            the API endpoint. Once the response is received, and this
            coroutine is the active coroutine in the event loop, call
            the 'handle_response_json' function to validate the
            response and save data to self.log_dictionary.

        Parameters
        ----------
        session: aiohttp.ClientSession object
            Used for non-blocking HTTP requests
        _params: dict
            Dictonary that contains parameters to be passed in the
            query string of the API call.
        """
        type_ = _params['type']
        need_recursion = False

        if pagination:
            logging.info('Async API with event type {} has more than {}'
                         ' events. Now making pagination request number {}'
                         ''.format(type_, self.max_logs, str(pagination)))
        else:
            logging.info('Calling Async API with event type {}'
                         ''.format(type_))

        if skip:
            _params['skip'] = skip

        async with session.get(self.url, params=_params) as r:
            json_ = await r.json()
            status_code = r.status

            if not self._status_check(json_, status_code):
                if pagination:
                    logging.error('Error with event type {} when pulling '
                                  'pagination {} of logs.'
                                  ''.format(type_, str(pagination)))
                return

            try:
                if len(json_['data']) >= self.max_logs:
                    need_recursion = True
            except KeyError:
                logging.error("Missing 'data' key in response for {}"
                              "".format(type_))
            else:
                if type_ not in self.log_dictionary.keys():
                    self.log_dictionary[type_] = []
                if need_recursion:
                    self.log_dictionary[type_] += json_['data']
                    next_skip = len(self.log_dictionary[type_])
                    pagination += 1
                    await self._api_call_2(
                        session, _params, pagination=pagination, skip=next_skip
                    )
                else:
                    self.log_dictionary[type_] += json_['data']

            if not skip:
                length = str(len(self.log_dictionary[type_]))
                logging.info('Consumed {} logs for type: {}'
                             ''.format(length, type_))

    def _status_check(self, json_, status_code):
        if (status_code != 200) or (json_['status'] != 'success'):
            # Log the issue
            logging.error('Response received from requests: '
                          '{}'.format(json.dumps(json_, indent=2)))
            return False
        return True

    def handle_response_json(self, type_, json_, status_code):
        """ Validate response and add to self.log_dict which will be
            used to write logs to file later.

        Parameters
        ----------
        type_: str
            Represents the 'type' of the log
        json_: dict
            Dictonary created from the response of the API call
        status_code: int
            The status code of the response
        """
        try:
            # {'type': [{log1}, {log2},...{logn}]}
            self.log_dictionary[type_] = json_['data']
            length = str(len(self.log_dictionary[type_]))
            logging.info('Consumed {} logs for type: {}'.format(length, type_))
        except KeyError as k:
            # No data, should at least be an empty list
            logging.error('{} log had no data field.'.format(type_))
