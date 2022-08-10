import base64
import json
from time import time
import requests
import subprocess

from walkoff_app_sdk.app_base import AppBase

class BeyondSecurity(AppBase):
    __version__ = "1.0.0"
    app_name = "SS - Beyond Security BeSecure"  

    def __init__(self, redis, logger, console_logger=None):
        print("INIT")
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)


    def splitheaders(self, headers):
        parsed_headers = {}
        if headers:
            split_headers = headers.split("\n") 
            self.logger.info(split_headers)
            for header in split_headers:
                if ": " in header:
                    splititem = ": "
                elif ":" in header:
                    splititem = ":"
                elif "= " in header:
                    splititem = "= "
                elif "=" in header:
                    splititem = "="
                else:
                    self.logger.info("Skipping header %s as its invalid" % header)
                    continue

                splitheader = header.split(splititem)
                if len(splitheader) == 2:
                    parsed_headers[splitheader[0]] = splitheader[1]
                else:
                    self.logger.info("Skipping header %s with split %s cus only one item" % (header, splititem))
                    continue

        return parsed_headers

    def checkverify(self, verify):
        if verify == None:
            return False
        elif verify:
            return True
        elif not verify:
            return False
        elif verify.lower().strip() == "false":
            return False
        else:
            return True 

    def checkbody(self, body):
        # Indicates json
        if body.strip().startswith("{"):
            body = body.replace("\'", "\"")

            # Not sure if loading is necessary
            # Seemed to work with plain string into data=body too, and not parsed json=body
            #try:
            #    body = json.loads(body) 
            #except json.decoder.JSONDecodeError as e:
            #    return body

            return body
        else:
            return body

    def fix_url(self, url):
        # Random bugs seen by users
        if "hhttp" in url:
            url = url.replace("hhttp", "http")

        if "http:/" in url and not "http://" in url:
            url = url.replace("http:/", "http://", -1)
        if "https:/" in url and not "https://" in url:
            url = url.replace("https:/", "https://", -1)
        if "http:///" in url:
            url = url.replace("http:///", "http://", -1)
        if "https:///" in url:
            url = url.replace("https:///", "https://", -1)
        if not "http://" in url and not "http" in url:
            url = f"http://{url}" 

        return url

    def POST(self, url, body="", verify=True):
        headers={"Content-Type": "application/x-www-form-urlencoded"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)

        return requests.post(url, headers=headers, data=body, verify=verify).text

    def get_account_details(self, api_key, url, search_email,verify=True):
        

        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = "primary=admin&secondary=accounts&action=returnaccounts&apikey=" + api_key + "&order=userid&search_limit=99&direction=down&search_email=" + search_email
        send_request = self.POST(url, body=body, verify=True)
        return send_request

    def create_account(self, api_key, username, password, retype_password, security_profile, url, user_profile="E513CAF7", language="2", timezone="UTC", verify=True):
        

        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        if security_profile == "Default":
            security_profile = "031F28B7"
        if security_profile == "Safe Systems Security Profile":
            security_profile = "031F28B7"
        body = "primary=admin&secondary=accounts&action=create&apikey=" + api_key + "&username=" + username + "&password=" + password + "&password_retype=" + retype_password + "&securityprofile=" + security_profile + "&userprofile=" + user_profile + "&language=" + language + "&timezone=" + timezone
        send_request = self.POST(url, body=body, verify=True)
        return send_request

    def delete_account(self, api_key, url, user_id, verify=True):
        

        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = "primary=admin&secondary=accounts&action=delete&apikey=" + api_key + "&id=" + user_id
        send_request = self.POST(url, body=body, verify=True)
        return send_request


    def get_contacts(self, api_key, url, verify=True):
        

        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = "primary=admin&secondary=contacts&action=returncontacts&apikey=" + api_key + "&search_limit=99"
        send_request = self.POST(url, body=body, verify=True)
        return send_request
        
        
    def create_contact(self, api_key, url, username, fullname, verify=True):
        

        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = "primary=admin&secondary=contacts&action=create&apikey=" + api_key + "&contact_email=" + username + "&contact_name=" + fullname + "&contact_country=US"
        send_request = self.POST(url, body=body, verify=True)
        return send_request

# Run the actual thing after we've checked params

if __name__ == "__main__":
    BeyondSecurity.run()
