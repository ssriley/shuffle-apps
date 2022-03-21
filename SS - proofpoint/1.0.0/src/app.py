import json
import requests
#from telnetlib import TLS


from walkoff_app_sdk.app_base import AppBase

class ProofPoint(AppBase):
    __version__ = "1.0.0"
    app_name = "SS - ProofPoint SmartSearch"  # this needs to match "name" in api.yaml

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    def search_email(
        self,
        username,
        password,
        server,
        port="10000",
        action=None,
        sending_host=None,
        email_subject=None,
        sending_ip=None,
        attachment_name=None,
        from_address=None,
        to_address=None,
        count=100
    ):
        url_base = "https://" + server + ":" + port + "/rest/v1/pss/filter"
        querystring = {
            'action': action,
            'host': sending_host,
            'subject': email_subject,
            'ip': sending_ip,
            'attach': attachment_name,
            'env_from': from_address,
            'env_rcpt': to_address,
            'count': count
        }
        headers = {"Accept": "application/json"}
        return requests.get(url_base,headers=headers,auth=(username,password),params=querystring,verify=False).json()

if __name__ == "__main__":
    ProofPoint.run()
