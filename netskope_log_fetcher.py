from datetime import datetime
import logging
import json
import os
import re

from dotenv import load_dotenv

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
            return None
        else:
            if time_stamp <= 0:
                time_stamp = None
            return time_stamp


def write_logs(netskope_object):
    current_directory = os.path.dirname(__file__)
    for type_, log_list in netskope_object.log_dictionary.items():
        file_ = replace_spaces(type_)
        # logs/alert or logs/event
        log_path = os.path.join('logs', netskope_object.endpoint_type)
        make_dir_if_needed(current_directory, log_path)
        # Ex: base/file/path/logs/alert/type.log
        log_file = os.path.join(current_directory, log_path, f'{file_}.log')

        with open(log_file, 'a+') as f:
            try:
                for log in log_list:
                    json_string = json.dumps(log)
                    f.write("{}\n".format(json_string))
            except TypeError as t:
                logging.warn(f'Couldn\'t write logs for {type_}: {t}')


def make_dir_if_needed(current_dir, log_dir):
    required_dir = os.path.join(current_dir, log_dir)
    if not os.path.isdir(required_dir):
        os.mkdir(required_dir)


def replace_spaces(some_string):
    return re.sub(' ', '_', some_string)


if __name__ == "__main__":

    setup_logger()

    current_directory = os.path.dirname(__file__)
    load_dotenv(dotenv_path=os.path.join(current_directory, '.env'))

    tiny_time = TinyTimeWriter()
    token = Token()

    end_time = int(datetime.now().timestamp())
    start_time = tiny_time.get_last_log_time() or (end_time - 600)

    logging.info(
        f'Running from '
        f'{datetime.strftime(datetime.fromtimestamp(end_time), "%c")} '
        f'to {datetime.strftime(datetime.fromtimestamp(start_time), "%c")}')

    clients = [
        EventClient(token=token, start=start_time, end=end_time),
        AlertClient(token=token, start=start_time, end=end_time),
    ]

    for client in clients:
        client.get_all_event_types()
        write_logs(client)

    tiny_time.save_last_log_time(end_time)

    exit()
