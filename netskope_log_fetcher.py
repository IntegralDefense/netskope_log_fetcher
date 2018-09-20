import os

from dotenv import load_dotenv

from netskope.token import Token

if __name__ == "__main__":

    current_directory = os.path.dirname(__file__)
    load_dotenv(dotenv_path=os.path.join(current_directory, '.env'))

    token = Token()
    
    


    # Setup client to hold auth token

    # Setup events

    # Setup alerts

    exit()