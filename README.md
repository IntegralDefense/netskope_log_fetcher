# netskope_log_fetcher

Asynchronous Python script to pull down Netskope CASB logs.

## Getting Started

1. Clone the repo:

    ```bash
    $ cd /your/repo/directory
    $ git clone git@github.com:IntegralDefense/netskope_log_fetcher.git
    $ cd netskope_log_fetcher
    ```
2. Create virtual environment and install requirements:

    ```bash
    $ python3 -m venv venv
 
    # Linux:
    $ source venv/bin/activate
 
    # OR if using Windows:
    > .\venv\Scripts\activate (if using windows)
 
    (venv) $ pip install -r requirements.txt
    ```

3. Create your `.env` file from the template file:

    ```bash
    (venv) $ cp .env.template .env
    ```

4. Configure your `.env` file to use your tenant name and Netskope token:

    ```ini
    # Your tenant name: https://<tenant-name>.goskope.com
    NETSKOPE_TENANT_NAME=<tenant-name>

    # Your Netskope auth token
    NETSKOPE_AUTH_TOKEN=<some_long_auth_token>

    # If no time.log file is available (stores the end timestamp of your last run),
    # how many seconds back do you want to search for logs?
    NETSKOPE_DEFAULT_INTERVAL=600
    ```

5. Run the script:

    ```bash
    (venv) $ python netskope_log_fetcher.py
    ```

### Prerequisites

Python 3.5+

## Running the tests

Sorry, no tests yet. Feel free to contribute!

## Deployment

If you deploy this script with a Cronjob, you must be aware that if the script runs
longer than your cron job interval, you may pull down duplicate logs or exhaust resources
by spawning multiple instance of the script unnecessarily.

A couple hints on how to avoid this:
1. Use 'flock' if available in your distribution.
    - Locks a file when the cron job runs.
    - If the cron job tries to start up again, flock will abort if the designated file already has a lock
    from the previous run.
2. Use a PID file.

#### Flock example:
1. Create an entry point for your python script. For example: create a shell script that
bootstraps the python script using your virtual environment:
<br>
<br>
    */opt/netskope_log_fetcher/netskope.sh*
    ```bash
    #!/usr/bin/bash

    /opt/netskope_log_fetcher/venv/bin/python /opt/netskope_log_fetcher/netskope_log_fetcher.py
    ```
2. Create an empty file to be used by flock for keeping up with the lock:
    ```bash
    $ touch netskope.lock
    ```
3. Setup your cron job:
    ```bash
    */10 * * * * /usr/bin/flock -n /opt/netskope_log_fetcher/netskope.lock /opt/netskope_log_fetcher/netskope.sh >> /some/cron/log/file.log 2>&1
    ```

## Contributing

For the sake of brevity in collaboration, use Pylint for linting and Black for formatting. Black and Pylint
don't always get along, so please disable pylint in-line where possible when it fights with Black.

Example of disabling a pylint warning:
```python
client = SomeClientObject(url="https://test.example.com/api1")

# The following in-line comment disables the 'protected-access' warning from
# pylint. This particular example is handy during unit testing where you may
# want to test your protected functions of a class.

client._protected_function()  # pylint: disable=protected-access
```

You'll notice there is currently a lack of tests for this script. Please add tests as you make changes.

Create an issue BEFORE making pull requests. When you make a pull request, please note which
issue your pull request fixes. For example: ```Fixed #22```.

## Testing

### Run tests

- Be sure that pylint, pylint-aiohttp, pylint-asyncio, and pylint-mock are installed and then
run the following:
    ```python
    $ cd /opt/netskope_log_fetcher
    $ source venv/bin/activate
    (venv) pytest tests/
    ```

### Notes about writing tests for async code

Be sure your tests of async functions are using the ```@pytest.mark.asyncio``` decorator to ensure
an event loop is properly available for your coroutine.

Testing asyncio functionality is not as straight forward as testing normal python code.
In the ```tests/helpers.py``` module, you will find a class called ```AsyncHelper```.
You may use this class to help mock return values that are being awaited.

For example, when you await the aiohttp.ClientResponse.json coroutine, your script expects
a co-routine. If you mock aiohttp.ClientResponse.json, and you return a normal function, your
tests may/may not fail. Sometimes, your tests will pass even though they shouldn't and you
may/may not receive a warning that your 'task' was never awaited.

When you are mocking something that is going to be awaited, you must return a coroutine.
This is where the AsyncHelper comes in handy:

```python
class AsyncHelper:
    """ Class wrapper for helper functions. When unit testing async
    style stuffz, an 'await' statement expects a coroutine; Therefore,
    we wrap the desired outcome with a coroutine. It's kind of like
    a mock for coroutines.
    """

    @staticmethod
    async def value(val):
        """ Coroutine wrapper for mocking with return values."""

        return val

    @staticmethod
    async def error(error, *args, **kwargs):
        """ Coroutine wrapper for mocking forced exceptions/errors."""

        raise error(*args, **kwargs)

# A fixture to make the async_helper accessible to the tests
@pytest.fixture(scope="module")
def async_helper():
    return AsyncHelper()

# Be sure that you make the 'return_values' of the coroutines your mocking
# so that they return one of our AyndHelper coroutines.
@pytest.mark.asyncio
async def test_handle_response_content_type_error_during_api_call(
    mocker, async_helper, req
):
    """Tests to see if BaseNetskopeClient._handle_response handles a\
    ContentTypeError properly.
    """

    config = {
        "json.return_value": async_helper.error(ContentTypeError, "Placeholder", ()),
        "text.return_value": async_helper.value(req.text),
        "status": req.status,
    }
    mocked = mocker.MagicMock(**config)
    with pytest.raises(ContentTypeError):
        await req.base_client._handle_response(  # pylint: disable=protected-access
            _params=req.params, _type=req.type_, _resp=mocked
        )
```

## Authors

* **Kyle Piper** - *Initial work* - [IntegralDefense](https://github.com/IntegralDefense)

## License

Apache 2.0 License
