
import os


class Token:
    """ Helper class to grap and store Netskop API auth token """

    def __init__(self, auth_token=None):
        """ Get auth token from environment variables"""

        self.auth_token = auth_token or os.environ['NETSKOPE_AUTH_TOKEN']
