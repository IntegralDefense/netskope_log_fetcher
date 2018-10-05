from datetime import datetime
import logging
import json
import os
import re

from dotenv import load_dotenv

from netskope_fetcher.bootstrap import NetskopeAsyncBootstrap
from netskope_fetcher.token import Token
from netskope_fetcher.events import EventClient
from netskope_fetcher.alerts import AlertClient
from netskope_fetcher.logger import setup_logger


class TinyTimeWriter:

    def __init__(self, file_path=None):
        self.time_file_path = (
            file_path or os.path.join(os.path.dirname(__file__), 'time.log'))

    def save_last_log_time(self, _time):
        """
        Saves the end-time defined for the current run of the program.
        Parameters
        ----------
        format_: str
            Format you wish the string output to be in
        Returns
        ----------
        datetime string
            String format of the datetime object.
        """
        with open(self.time_file_path, 'w') as _file:
            _file.write(str(_time))

    def get_last_log_time(self):
        """ Reads the last log time from file

        Returns
        ----------
        Epoch time stamp for last time the program ran.
        """
        try:
            with open(self.time_file_path, 'r') as _file:
                time_stamp = int(_file.readline())
        except FileNotFoundError:
            # File doesn't exist yet
            return None
        except ValueError:
            # If non-int or empty file.
            return None
        else:
            if time_stamp <= 0:
                time_stamp = None
            return time_stamp


def write_logs(netskope_object):
    """ Writes logs to the type-specific log file.

        Pull the log files from netskope_object.log_dictionary, and
        write them to file.  If log_dictionary looks like this:
        {
            'application': [list of logs],
            'page': [list of logs],
        }
        Then this is an 'EventClient' object and we will write to two
        files like this:

        /file/path/to/logs/event/application.log
        and
        /file/path/to/logs/event/page.log

    Parameters
    ----------
    netskope_object: netskope_fetcher.events.EventClient
                     OR netskope_fetcher.alerts.AlertClient
        Object contains the log files in log_dictionary.
    """

    current_directory = os.path.dirname(__file__)
    for type_, log_list in netskope_object.log_dictionary.items():
        # Some types have spaces, replace them with underscores
        file_ = replace_spaces(type_)
        # logs/alert or logs/event
        log_path = os.path.join('logs', netskope_object.endpoint_type)
        make_dir_if_needed(current_directory, log_path)
        # Ex: base/file/path/logs/alert/type.log
        log_file = os.path.join(current_directory, log_path, '{}.log'.format(file_))

        with open(log_file, 'a+') as f:
            logging.debug('Writing to {} log file'.format(log_file))
            try:
                for log in log_list:
                    f.write('{}\n'.format(json.dumps(log))
            except TypeError as t:
                # Most likely that log_list is not an iterable
                logging.warn('Couldn\'t write logs for {}: {}'
                             ''.format(type_, {t}))


def make_dir_if_needed(current_dir, log_dir):
    """ Helper function to create approriate log directories if they
        don't already exist

    Parameters
    ----------
    current_dir: str
        /path/to/current/directory
    log_dir: str
        logs/event or logs/alert. Will be appended to current_dir
    """

    required_dir = os.path.join(current_dir, log_dir)
    if not os.path.isdir(required_dir):
        os.mkdir(required_dir)


def replace_spaces(some_string):
    """ Substitute spaces with underscores"""

    return re.sub(' ', '_', some_string)


if __name__ == "__main__":
    try:
        setup_logger()

        current_directory = os.path.dirname(__file__)
        load_dotenv(dotenv_path=os.path.join(current_directory, '.env'))

        tiny_time = TinyTimeWriter()
        token = Token()

        # End time will always be 'right now'
        # start_time will be the end of the last successful run, or in the
        #    case that the last timestamp isn't available, set the start
        #    time to ten minutes ago.
        end_time = int(datetime.now().timestamp())
        start_time = tiny_time.get_last_log_time() or (end_time - 600)

        logging.info('Running from {} to {}'.format(
                datetime.strftime(datetime.fromtimestamp(start_time), "%c"),
                datetime.strftime(datetime.fromtimestamp(end_time), "%c")
            ))

        clients = [
            EventClient(token=token, start=start_time, end=end_time),
            AlertClient(token=token, start=start_time, end=end_time),
        ]

        bootstrap = NetskopeAsyncBootstrap(client_list=clients)
        bootstrap.run()

        # Write to the log files
        for client in clients:
            write_logs(client)

        # Save the end time so that it can be used in the next run.
        # This is purposely left at the end of the program so that the
        # subsequent run of the program will gather logs that may have been
        # missed if the script were to fail mid-stream.
        tiny_time.save_last_log_time(end_time)
    except Exception as e:
        logging.exception('Exception Occured')
        raise

    exit()
