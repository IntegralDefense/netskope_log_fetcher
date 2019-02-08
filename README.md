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

Check yo' self with PyLint,<br>
format with Black.<br>
Thanks for contributing,<br>
pat yourself on the back.

If you wish to fix something,<br>
open an issue.<br>
Once you have it fixed,<br>
pull request with 'Fixed #<num_issue>'.

Ex: "Fixed #22"

## Authors

* **Kyle Piper** - *Initial work* - [IntegralDefense](https://github.com/IntegralDefense)

## License

Apache 2.0 License
