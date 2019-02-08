"""Defines the base Netskope client class and all attributes,
functions, and coroutines required to asynchronously interact with the
Netskope API."""

from datetime import datetime
import asyncio
import logging
import json
import os

from aiohttp.client_exceptions import ContentTypeError


def _status_check(json_, type_, status_code, pagination):
    """ Check to see if response is valid or un-expected """

    if (status_code != 200) or (json_["status"] != "success"):
        # Log the issue
        logging.error(
            "Response received from requests: %s", json.dumps(json_, indent=2)
        )
        # If we're pulling down the extended logs (over max limit)
        #    then we want to note that in the logs so we can tell
        #    that we received some of the logs but not all of them.
        if pagination:
            logging.error(
                "Error with event type %s when pulling pagination %s of logs.",
                type_,
                str(pagination),
            )
        return False
    return True


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
    max_logs: int
        The maximum amount of logs before pagination must be performed.
    """

    def __init__(self, **kwargs):
        self.token = kwargs.get("token")
        self.end = kwargs.get("end") or int(datetime.now().timestamp())
        self.start = kwargs.get("start") or (
            self.end - int(os.environ["NETSKOPE_DEFAULT_INTERVAL"])
        )
        self.type_list = []
        self.log_dictionary = {}
        self.session = kwargs.get("session")
        self.url = kwargs.get("url")
        self.max_logs = 5000  # TODO - move this to config file

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

        tasks = [self._async_worker(session, type_) for type_ in self.type_list]
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
            "token": self.token.auth_token,
            "type": event_type,
            "starttime": self.start,
            "endtime": self.end,
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
        type_ = _params["type"]
        need_recursion = False

        # If this is a recursive call to pull down more logs for a
        # particular type, then make sure the logs reflect it.
        self._log_api_call_context(type_, pagination)

        # If skip is defined, then this is a second pass at pulling
        # down logs that couldn't be grabbed in the original call.
        # Add the skip value to the parameters so netskope will not
        # return logs we have already received.
        if skip:
            _params["skip"] = skip

        # Start async session to pull down logs.
        async with session.get(self.url, params=_params) as resp:

            status_code = resp.status

            try:
                json_ = await resp.json()

            except ContentTypeError:
                text = await resp.text()

                # Remove token parameter since we'll be writing this to
                # log file.
                filtered_params = {
                    param: value for param, value in _params.items() if param != "token"
                }

                # This info will give our logs context as to what caused
                # the error.
                error = {
                    "status_code": status_code,
                    "response": text,
                    "url_requested": self.url,
                    "query_parameters": filtered_params,
                }
                logging.error(
                    "Unexpected response when pulling logs for %s: %s",
                    type_,
                    json.dumps(error, indent=2),
                )

                # Let this bubble up and stop the program. We don't want
                # to miss these logs because of the time file being
                # updated if this script were to complete.
                raise

            else:

                # Check to make sure status was 200 or 'success'
                if not _status_check(json_, type_, status_code, pagination):
                    return

                # Did we hit our log limit in the response and need to go
                # grab more?  (Also tests if data was returned or not)
                if self._api_has_more_logs_to_grab(json_, type_):
                    need_recursion = True

                # Initializing an empty list enables us to just use one
                # '+=' line to add initial logs or supplemental logs
                # (logs we had to go back and get due to the log
                # limit in the response)
                self._prep_type_if_no_logs_already_present(type_)

                # And since we have the former function, we can do this.
                # It covers both first and recursive calls.
                self.log_dictionary[type_] += json_["data"]

                # If we need to, pull down supplemental logs.
                if need_recursion:
                    await self._get_remaining_logs(type_, session, _params, pagination)

                # If this is NOT a supplemental request for logs, we can
                # now know the total count of the logs we pulled down for
                # this type.
                if not skip:
                    length = str(len(self.log_dictionary[type_]))
                    logging.info("Consumed %s logs for type: %s", length, type_)

    async def _get_remaining_logs(self, type_, session, _params, pagination):
        """ Make another call to pull down the remaining logs for the
            current type.
        """

        next_skip = len(self.log_dictionary[type_])
        pagination += 1
        await self._api_call_2(session, _params, pagination=pagination, skip=next_skip)

    def _api_has_more_logs_to_grab(self, json_, type_):
        """ Two purposes:
                1. Check to see if we need to make further
                   calls to acquire all the logs available for the
                   current time frame.
                2. See if the log 'data' is missing from the Netskope
                   response.
        Parameters
        ----------
        json_: dict
            Dictionary of the response from Netskope API

        Returns
        ----------
        bool
            True: We received the maximum # of logs the response should
                  contain (Need to go back and pull more logs).
            False: We received all logs available for this type.
        """

        try:
            return len(json_["data"]) >= self.max_logs
        except KeyError:
            logging.error("Missing 'data' key in response for %s", type_)

    def _prep_type_if_no_logs_already_present(self, type_):
        """ Initialize a list for the current type """

        if type_ not in self.log_dictionary.keys():
            self.log_dictionary[type_] = []

    def _log_api_call_context(self, type_, pagination):
        """ If this is a recursive call to pull down more logs for a
            particular type, then make sure the logs reflect it. We can
            tell if this is a second+ call to the API for a type by
            checking to see if pagination is anything other than '0'.

        Parameters
        ----------
        type_: str
            Representation of the 'type' of log we're pulling down.
        pagination: int
            0 if this is not a secondary call to Netskope to pull down
            more logs due to limit of the original call. >0 if this is
            a secondary call to gather all logs available.
        """

        if pagination:
            logging.info(
                "Async API with event type %s has more than %s"
                " events. Now making pagination request number %s",
                type_,
                self.max_logs,
                str(pagination),
            )
        else:
            logging.info("Calling Async API with event type %s.", type_)

    def handle_response_json(self, type_, json_):
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
            self.log_dictionary[type_] = json_["data"]
            length = str(len(self.log_dictionary[type_]))
            logging.info("Consumed %s logs for type: %s", length, type_)
        except KeyError:
            # No data, should at least be an empty list
            logging.error("%s log had no data field.", type_)
