from datetime import datetime
import json
import os

from dotenv import load_dotenv

from netskope_fetcher.token import Token
from netskope_fetcher.events import EventClient
from netskope_fetcher.alerts import AlertClient


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
        log_file = os.path.join(current_directory, "{}.log".format(type_))
        with open(log_file, 'a+') as f:
            for log in log_list:
                json_string = json.dumps(log)
                f.write("{}\n".format(json_string))


if __name__ == "__main__":

    current_directory = os.path.dirname(__file__)
    load_dotenv(dotenv_path=os.path.join(current_directory, '.env'))

    tiny_time = TinyTimeWriter()
    token = Token()

    end_time = int(datetime.now().timestamp())
    start_time = tiny_time.get_last_log_time() or (end_time - 600)

    clients = [
        EventClient(token=token, start=start_time, end=end_time),
        AlertClient(token=token, start=start_time, end=end_time),
    ]

    for client in clients:
        client.get_all_event_types()

    map(write_logs, clients)

    tiny_time.save_last_log_time(end_time)

    exit()
