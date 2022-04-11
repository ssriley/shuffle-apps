
import datetime
import random
import string

from walkoff_app_sdk.app_base import AppBase


class SS_Tools(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console
    logging set up behind the scenes.
    """

    __version__ = "1.0.0"
    app_name = (
        "SS_Tools"  # this needs to match "name" in api.yaml for WALKOFF to work
    )

    def __init__(self, redis, logger, console_logger=None):
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
        result = {"random_password": password}
        return result

    def convert_epoch_to_datetime(self,epoch):
        my_datetime = datetime.datetime.fromtimestamp(int(epoch)).strftime('%c')
        return my_datetime

if __name__ == "__main__":
    SS_Tools.run()
