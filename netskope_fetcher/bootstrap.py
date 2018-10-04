
import asyncio
import aiohttp


class NetskopeAsyncBootstrap:
    """ Helper class that bootstraps the Async http calls to the
        netskope API.
    """

    def __init__(self, client_list):
        """
        Parameters
        ----------
        client_list: list
            List of netskope_fetcher.base.BaseNetskopeClient children
        """

        self.client_list = client_list

    def run(self):
        """ Sets up the asyncio event loop and then starts it.

            First coroutine added to the event loop is passed the loop
            which will be used to add further tasks and aiohttp client session
            to the loop that is currently running
        """

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.run_async_clients(loop))

    async def run_async_clients(self, loop):
        """ Sets up client session to be used by all aiohttp calls.

            Gets a list of the coroutines for each client which will be
            added to the event loop (passes them the current loop and
            the session) then awaits all of them.
        """

        async with aiohttp.ClientSession(loop=loop) as session:
            # Clients are children of
            # netskope_fetcher.base.BaseNetskopeClient
            tasks = [
                client.get_logs(session, loop) for client in self.client_list
            ]
            await asyncio.gather(*tasks, loop=loop)
