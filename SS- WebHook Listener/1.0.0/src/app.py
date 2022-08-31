
import datetime
from logging import exception
import xmltodict
import json
from flask import Flask, request, Response

from walkoff_app_sdk.app_base import AppBase


class SS_Webhook_Listener(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console
    logging set up behind the scenes.
    """

    __version__ = "1.0.0"
    app_name = (
        "SS - Webhook_Listener"  # this needs to match "name" in api.yaml for WALKOFF to work
    )

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    def listen(self,port=9999,custom_response="ack=true"):
        app = Flask(__name__)

        @app.route('/', methods=['POST'])
        def respond():
            print(request.json)
            return Response(status=200, data=custom_response)
        app.run(host='0.0.0.0', port=port)
    def salesforce_to_json(self,xml):
        xml_to_json_org = xmltodict.parse(xml)
        #return xml_to_json['soapenv:Envelope']['soapenv:Body']['notifications']['notification']
        try:
            xml_to_json = xml_to_json_org['soapenv:Envelope']['soapenv:Body']['notifications']['Notification']
            xml_str = json.dumps(xml_to_json).replace('sf:', '')
            xml_str = xml_str.replace('__c', '')
            xml_str = xml_str.replace('_', '')
            return json.loads(xml_str)
        except exception as e:
            return xml_to_json_org


if __name__ == "__main__":
    SS_Webhook_Listener.run()
