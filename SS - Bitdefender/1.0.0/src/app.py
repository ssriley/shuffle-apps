import base64
import json
import requests
import subprocess

from walkoff_app_sdk.app_base import AppBase

class Bitdefender(AppBase):
    __version__ = "1.0.0"
    app_name = "SS - Bitdefender"  

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

    def POST(self, url, headers="", body={}, username="", password="", verify=True, method=None):
        #url = self.fix_url(url)
        password_bytes = password.encode('ascii')
        base64_bytes = base64.b64encode(password_bytes)
        base64_string = base64_bytes.decode('ascii')
        headers={"Content-Type": "application/json",
        "Authorization": "Basic " + base64_string + "="
        }
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        payload = {
            "id": "2bc99d4c804576e0cd7b1b1463ce479e",
            "jsonrpc": "2.0",
            "method": method,
            "params": body
        }
        return requests.post(url, headers=headers, json=payload, verify=verify).text

    # UNTESTED BELOW HERE
    def get_push_event_settings(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/push"

        #parsed_headers = self.splitheaders(headers)
        headers={"Content-Type": "application/json"}
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getPushEventSettings")
        return send_request

    def set_event_settings(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/push"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="setPushEventSettings")
        return send_request

    def get_account_list(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/accounts"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getAccountsList")
        return send_request

    def update_user_account(self, body={}, username="", password="", verify=True, account_id=None, email=None, bd_password=None):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/accounts"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        if bd_password is not None and email is not None:
            body = {
                "accountId": account_id,
                "email": email,
                "password": bd_password
            }
        elif email is not None:
            body = {
                "accountId": account_id,
                "email": email
            }
        elif bd_password is not None:
            body = {
                "accountId": account_id,
                "password": bd_password
            }

        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="updateAccount")
        return send_request

    def delete_user_account(self, body={}, username="", password="", verify=True, account_id=None):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/accounts"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
            "accountId": account_id
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="deleteAccount")
        return send_request

    def create_user_account(self, body={}, username="", password="", verify=True, email="", fullName="",bd_password=None,role=None):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/accounts"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        if role == "company_administrator":
            role = 1
        elif role == "network_administrator":
            role = 2
        elif role == "reporter":
            role = 3
        elif role == "partner":
            role = 4
        body = {
           "email": email,
           "profile": {
               "fullName": fullName,
               "language": "en_US",
               "timezone": "America/New_York"
           },
           "password": bd_password,
           "role": role
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="createAccount")
        return send_request

    def send_test_push_event(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/push"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="sendTestPushEvent")
        return send_request

    def get_push_event_stats(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/push"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getPushEventStats")
        return send_request

    def get_policy_list(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/policies/"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getPoliciesList")
        return send_request

    def get_policy_details(self, body={}, username="", password="", verify=True, policy_id=""):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/policies/"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
            "policyId": policy_id
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getPolicyDetails")
        return send_request

    def get_endpoint_list(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/network"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getEndpointsList")
        return send_request

    def get_endpoint_details(self, body={}, username="", password="", verify=True, filters=None):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/network"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
            "filters": {
                "details": {
                    "name": filters
                }
            }
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getManagedEndpointDetails")
        return send_request

    def get_company_list(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/network"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getManagedEndpointDetails")
        return send_request

    def add_to_block_list(self, body={}, username="", password="", verify=True, hash_type="",hash_list=None,source_info=""):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/incidents"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        if hash_type == "sha256":
            hash_type = 1
        if hash_type == "md5":
            hash_type = 2
        try:
            #input_list = eval(input_list)  # nosec
            hash_list = json.loads(hash_list)
        except Exception:
            try:
                hash_list = hash_list.replace("'", '"', -1)
                hash_list = json.loads(hash_list)
            except Exception:
                print("[WARNING] Error parsing string to array. Continuing anyway.")

        # Workaround D:
        if not isinstance(hash_list, list):
            return {
                "success": False,
                "reason": "Error: input isnt a list. Remove # to use this action.", 
                "valid": [],
                "invalid": [],
            }

        hash_list = [hash_list]
        body = {
            "hashType": hash_type,
            "hashList": hash_list,
            "sourceInfo": source_info
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="addToBlocklist")
        return send_request

    def get_block_list_items(self, body={}, username="", password="", verify=True):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/incidents"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="getBlocklistItems")
        return send_request

    def remove_from_block_list(self, body={}, username="", password="", verify=True, hash_item_id=""):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/incidents"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
            "hashItemId": hash_item_id
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="removeFromBlocklist")
        return send_request

    def isolate_endpoint(self, body={}, username="", password="", verify=True, endpoint_id=""):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/incidents"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
            "endpointId": endpoint_id
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="createIsolateEndpointTask")
        return send_request

    def restore_isolated_endpoint(self, body={}, username="", password="", verify=True, endpoint_id=""):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/incidents"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        body = {
            "endpointId": endpoint_id
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="createRestoreEndpointFromIsolationTask")
        return send_request

    def create_connection_edr_rule(self, 
    body={}, 
    username="", 
    password="", 
    verify=True, 
    rule_type=None, 
    rule_name="", 
    rule_description=None,
    field_1=None,
    relation_1=None,
    value_1=None,
    field_2=None,
    relation_2=None,
    value_2=None,
    field_3=None,
    relation_3=None,
    value_3=None):
        url = "https://cloud.gravityzone.bitdefender.com/api/v1.0/jsonrpc/incidents"
        headers={"Content-Type": "application/json"}
        #parsed_headers = self.splitheaders(headers)
        verify = self.checkverify(verify)
        #body = self.checkbody(body)
        criteria_list = [{
            "field": "Connection." + field_1,
            "relation": "Connection." + relation_1,
            "value": [value_1]
        },
        {
            "field": "Connection." + field_2,
            "relation": "Connection." + relation_2,
            "value": [value_2]
        },
        {
            "field": "Connection." + field_3,
            "relation": "Connection." + relation_3,
            "value": [value_3]
        }]
        if rule_type == "detection":
            rule_type = 1
        if rule_type == "exclusion":
            rule_type = 2
        body = {
            "type": rule_type,
            "name": rule_name,
            "description": rule_description,
            "settings": {
                "status": 0,
                "severity": 1,
                "target": "connection",
                "criteriaList": criteria_list
            }
        }
        send_request = self.POST(url, headers=headers, body=body, username=username, password=password, verify=True, method="createRestoreEndpointFromIsolationTask")
        return send_request

# Run the actual thing after we've checked params

if __name__ == "__main__":
    Bitdefender.run()
