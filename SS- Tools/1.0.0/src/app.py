
import datetime
from logging import exception
import random
import string
import xmltodict
import json
import uuid

from walkoff_app_sdk.app_base import AppBase


class SS_Tools(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console
    logging set up behind the scenes.
    """

    __version__ = "1.0.0"
    app_name = (
        "SS - Tools"  # this needs to match "name" in api.yaml for WALKOFF to work
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
        result = {"password": password}
        return result

    def convert_epoch_to_datetime(self,epoch):
        my_datetime = datetime.datetime.utcfromtimestamp(int(epoch)).strftime('%Y-%m-%dT%H:%M:%S')
        #my_datetime = datetime.datetime.utcfromtimestamp(int(epoch))
        return {"date": my_datetime}

    def convert_xml_to_json(self,xml):
        xml_to_json_org = xmltodict.parse(xml)
        #return xml_to_json['soapenv:Envelope']['soapenv:Body']['notifications']['notification']
        try:
            xml_to_json = xml_to_json_org['soapenv:Envelope']['soapenv:Body']['notifications']['Notification']
            xml_str = json.dumps(xml_to_json).replace('sf:', ' ')
            return json.loads(xml_str)
        except exception as e:
            return xml_to_json_org

    def generate_uuid_hex(self):
        return {"uuid": uuid.uuid4().hex}

if __name__ == "__main__":
    SS_Tools.run()
