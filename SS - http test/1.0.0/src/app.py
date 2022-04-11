import time
import json
import json
import random
import socket
import uncurl
import asyncio
import requests
import subprocess
import datetime
import random
import string

from walkoff_app_sdk.app_base import AppBase

class Test(AppBase):
    __version__ = "1.0.0"
    app_name = "SS - http test"  

    def __init__(self, redis, logger, console_logger=None):
        print("INIT")
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    def generate_password(self,length):
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for i in range(int(length)))
        result = {"password": password}
        return result

    def convert_epoch_to_datetime(self,epoch):
        my_datetime = datetime.datetime.fromtimestamp(int(epoch)).strftime('%c')
        return my_datetime
    
    def repeat_to_me(self,phrase):
        return phrase

if __name__ == "__main__":
    Test.run()
