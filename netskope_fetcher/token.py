
import os


class Token:

    def __init__(self, auth_token=None):
        self.auth_token = auth_token or os.environ['NETSKOPE_AUTH_TOKEN']
