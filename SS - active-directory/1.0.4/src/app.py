from dis import dis
import json
from operator import mod
#from telnetlib import TLS
import ssl
from typing import Any
import ldap3
import asyncio
from ldap3 import (
    Server,
    Connection,
    Tls,
    MODIFY_REPLACE,
    ALL_ATTRIBUTES,
    MODIFY_ADD,
    MODIFY_DELETE
)
from walkoff_app_sdk.app_base import AppBase

class ActiveDirectory(AppBase):
    __version__ = "1.0.4"
    app_name = "SS - Active Directory"  # this needs to match "name" in api.yaml

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    def __ldap_connection(self, server, port, domain, login_user, password, use_ssl,tls_validate=ssl.CERT_NONE,tls_version=ssl.PROTOCOL_TLSv1_2):
        use_SSL = False if use_ssl.lower() == "false" else True
        login_dn = domain + "\\" + login_user
        tls_config = Tls(validate=tls_validate,version=tls_version)
        s = Server(server, port=int(port), use_ssl=use_SSL, tls=tls_config)
        c = Connection(s, user=login_dn, password=password, auto_bind=True)

        return c

    # Decode UserAccountControl code
    def __getUserAccountControlAttributes(self, input_code):
        userAccountControlFlags = {
            16777216: "TRUSTED_TO_AUTH_FOR_DELEGATION",
            8388608: "PASSWORD_EXPIRED",
            4194304: "DONT_REQ_PREAUTH",
            2097152: "USE_DES_KEY_ONLY",
            1048576: "NOT_DELEGATED",
            524288: "TRUSTED_FOR_DELEGATION",
            262144: "SMARTCARD_REQUIRED",
            131072: "MNS_LOGON_ACCOUNT",
            65536: "DONT_EXPIRE_PASSWORD",
            8192: "SERVER_TRUST_ACCOUNT",
            4096: "WORKSTATION_TRUST_ACCOUNT",
            2048: "INTERDOMAIN_TRUST_ACCOUNT",
            512: "NORMAL_ACCOUNT",
            256: "TEMP_DUPLICATED_ACCOUNT",
            128: "ENCRYPTED_TEXT_PWD_ALLOWED",
            64: "PASSWD_CANT_CHANGE",
            32: "PASSWD_NOTREQD",
            16: "LOCKOUT",
            8: "HOMEDIR_REQUIRED",
            2: "ACCOUNTDISABLED",
            1: "SCRIPT",
        }
        lists = []
        attributes = {}
        while input_code > 0:
            for flag, flagName in userAccountControlFlags.items():
                temp = input_code - flag
                if temp > 0:
                    attributes[userAccountControlFlags[flag]] = flag
                    input_code = temp
                if temp == 0:
                    try:
                        if userAccountControlFlags[input_code]:
                            attributes[userAccountControlFlags[input_code]] = input_code
                    except KeyError:
                        pass
                    input_code = temp
        for key, val in attributes.items():
            lists.append(key)
        return lists

    # Encode UserAccountControl attributes
    def __getUserAccountControlCode(self, input_attributes):
        userAccountControlFlags = {
            "TRUSTED_TO_AUTH_FOR_DELEGATION": 16777216,
            "PASSWORD_EXPIRED": 8388608,
            "DONT_REQ_PREAUTH": 4194304,
            "USE_DES_KEY_ONLY": 2097152,
            "NOT_DELEGATED": 1048576,
            "TRUSTED_FOR_DELEGATION": 524288,
            "SMARTCARD_REQUIRED": 262144,
            "MNS_LOGON_ACCOUNT": 131072,
            "DONT_EXPIRE_PASSWORD": 65536,
            "SERVER_TRUST_ACCOUNT": 8192,
            "WORKSTATION_TRUST_ACCOUNT": 4096,
            "INTERDOMAIN_TRUST_ACCOUNT": 2048,
            "NORMAL_ACCOUNT": 512,
            "TEMP_DUPLICATED_ACCOUNT": 256,
            "ENCRYPTED_TEXT_PWD_ALLOWED": 128,
            "PASSWD_CANT_CHANGE": 64,
            "PASSWD_NOTREQD": 32,
            "LOCKOUT": 16,
            "HOMEDIR_REQUIRED": 8,
            "ACCOUNTDISABLED": 2,
            "SCRIPT": 1,
        }
        code = 0
        for attribute in input_attributes:
            code += userAccountControlFlags[attribute]

        return code

    # Get User Attributes
    def user_attributes(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        samaccountname,
        search_base,
    ):
        if search_base:
            base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)
        try:
            c.search(
                search_base=base_dn,
                search_filter=f"(samAccountName={samaccountname})",
                attributes=ALL_ATTRIBUTES,
            )
            result = json.loads(c.response_to_json())["entries"][0]
            result["attributes"][
                "userAccountControl"
            ] = self.__getUserAccountControlAttributes(
                result["attributes"]["userAccountControl"]
            )

            return json.dumps(result)
        except Exception as err:
            not_found = {"result": "User_Not_Found"}
            return not_found

    # Change User Password
    def set_password(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        samaccountname,
        new_password,
        repeat_password,
        search_base,
    ):
        if search_base:
            base_dn = search_base

        if new_password != repeat_password:
            return "Password does not match!"
        else:
            c = self.__ldap_connection(
                server, port, domain, login_user, password, use_ssl
            )

            result = json.loads( self.user_attributes( server, port, domain, login_user, password, base_dn, use_ssl, samaccountname, search_base,))

            user_dn = result["dn"]
            c.extend.microsoft.modify_password(user_dn, new_password)

            return json.dumps(c.result)

    # Change User Password at Next Logon
    def change_password_at_next_logon(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        samaccountname,
        search_base,
    ):
        if search_base:
            base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)

        result = json.loads(
            self.user_attributes(
                server,
                port,
                domain,
                login_user,
                password,
                base_dn,
                use_ssl,
                samaccountname,
                search_base,
            )
        )
        userAccountControl = result["attributes"]["userAccountControl"]

        if "DONT_EXPIRE_PASSWORD" in userAccountControl:
            return "Error: Flag DONT_EXPIRE_PASSWORD is set."
        else:
            user_dn = result["dn"]
            password_expire = {"pwdLastSet": (MODIFY_REPLACE, [0])}
            c.modify(dn=user_dn, changes=password_expire)
            c.result["samAccountName"] = samaccountname

            return json.dumps(c.result)

    # Enable User
    def enable_user(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        samaccountname,
        search_base,
    ):

        if search_base:
            base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)

        result = json.loads(
            self.user_attributes(
                server,
                port,
                domain,
                login_user,
                password,
                base_dn,
                use_ssl,
                samaccountname,
                search_base,
            )
        )
        userAccountControl = result["attributes"]["userAccountControl"]

        if "ACCOUNTDISABLED" in userAccountControl:
            userAccountControl.remove("ACCOUNTDISABLED")
            userAccountControl_code = self.__getUserAccountControlCode(
                userAccountControl
            )
            new_userAccountControl = {
                "userAccountControl": (MODIFY_REPLACE, userAccountControl_code)
            }
            user_dn = result["dn"]
            c.modify(dn=user_dn, changes=new_userAccountControl)
            c.result["samAccountName"] = samaccountname

            return json.dumps(c.result)
        else:
            result = {}
            result["samAccountName"] = samaccountname
            result["status"] = "success"
            result["description"] = "Account already enable"

            return json.dumps(result)

    # Disable User
    def disable_user(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        samaccountname,
        search_base,
    ):

        if search_base:
            base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)

        result = json.loads(
            self.user_attributes(
                server,
                port,
                domain,
                login_user,
                password,
                base_dn,
                use_ssl,
                samaccountname,
                search_base,
            )
        )
        userAccountControl = result["attributes"]["userAccountControl"]

        if "ACCOUNTDISABLED" in userAccountControl:
            result = {}
            result["samAccountName"] = samaccountname
            result["status"] = "success"
            result["description"] = "Account already disable"

            return json.dumps(result)
        else:
            userAccountControl.append("ACCOUNTDISABLED")
            userAccountControl_code = self.__getUserAccountControlCode(
                userAccountControl
            )
            new_userAccountControl = {
                "userAccountControl": (MODIFY_REPLACE, userAccountControl_code)
            }
            user_dn = result["dn"]
            c.modify(dn=user_dn, changes=new_userAccountControl)
            c.result["samAccountName"] = samaccountname

            return json.dumps(c.result)

    def group_attributes(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        groupname,
        search_base,
    ):
        if search_base:
            base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)

        c.search(
            search_base=base_dn,
            search_filter=f"(cn={groupname})",
            attributes=ALL_ATTRIBUTES,
        )
        result = json.loads(c.response_to_json())["entries"][0]

        result = {
            "group_name": result['attributes']['distinguishedName'],
            "group_members": result['attributes']['member'],
            'group_member_total': len(result['attributes']['member'])
        }
        #print(str(result))
        return json.dumps(result)

    def create_user(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        base_dn,
        use_ssl,
        samaccountname,
        firstname,
        lastname,
        email,
        upn_suffix,
        organizational_unit='ou=onboarding',
        home_drive='Z:',
        home_directory=None
    ):


        c = self.__ldap_connection(
            server, port, domain, login_user, password, use_ssl
        )
        conn = self.__ldap_connection(
            server, port, domain, login_user, password, use_ssl
        )
        c.add('cn=' + samaccountname + ',' + organizational_unit + ',' + base_dn, ['top', 'person', 'user', 'organizationalPerson'], 
        {'userPrincipalName': samaccountname + upn_suffix, 'sAMAccountName': samaccountname, 'givenName': firstname, 'sn': lastname, 'mail': email, 'displayName': firstname + ' ' + lastname, 'name': firstname + ' ' + lastname, 'homeDirectory': home_directory, 'homeDrive': home_drive})

        c.search(
            search_base=base_dn,
            search_filter=f"(cn={samaccountname})",
            attributes=ALL_ATTRIBUTES,
        )
        result = json.loads(c.response_to_json())["entries"][0]
        
        account_name = result['attributes']['distinguishedName']

        displayName = firstname + ' ' + lastname

        #c.modify(account_name,{'name': [(MODIFY_REPLACE, [displayName])]})

        c.modify_dn(account_name, 'cn=' + displayName)

        # need to get the new distinguished name after renaming it
        conn.search(
            search_base=base_dn,
            search_filter=f"(cn={samaccountname})",
            attributes=ALL_ATTRIBUTES,
        )

        dn_result = json.loads(c.response_to_json())["entries"][0]
        
        new_dn_name = dn_result['attributes']['distinguishedName']

        modify_result = c.result['description']
        #print(c.result)
        user_create_result = json.dumps(c.result)
        full_return = {
            'samaccountname': samaccountname,
            'firstname': firstname,
            'lastname': lastname,
            'email': email,
            'upn_suffix': upn_suffix,
            'organization_unit': organizational_unit,
            'result_of_operation': user_create_result,
            'home_directory': home_directory,
            'home_drive': home_drive,
            'display_name': displayName,
            'cn': new_dn_name,
            'dn_name_rename_result': modify_result
        }
        return json.dumps(full_return)
    
    def add_group_member(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        use_ssl,
        distinguished_groupname,
        distinguished_username
    ):
        # if search_base:
        #     base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)

        # c.search(
        #     search_base=base_dn,
        #     search_filter=f"(cn={groupname})",
        #     attributes=ALL_ATTRIBUTES,
        # )
        # result = json.loads(c.response_to_json())["entries"][0]

        # group_name = result['attributes']['distinguishedName']
        # c.search(
        #     search_base=base_dn,
        #     search_filter=f"(cn={samaccountname})",
        #     attributes=ALL_ATTRIBUTES,
        # )
        # result = json.loads(c.response_to_json())["entries"][0]
        
        # account_name = result['attributes']['distinguishedName']

        c.modify(distinguished_groupname,{'member': [(MODIFY_ADD, [distinguished_username])]})

        modify_result = c.result['description']
        final_result = {
            'action': 'Add user to Group',
            'result': modify_result,
            'group_name': distinguished_groupname,
            'user_name': distinguished_username
        }
        #print(str(final_result))
        return json.dumps(final_result)

    def delete_group_member(
        self,
        server,
        port,
        domain,
        login_user,
        password,
        use_ssl,
        distinguished_groupname,
        distinguished_username
    ):
        # if search_base:
        #     base_dn = search_base

        c = self.__ldap_connection(server, port, domain, login_user, password, use_ssl)

        # c.search(
        #     search_base=base_dn,
        #     search_filter=f"(cn={groupname})",
        #     attributes=ALL_ATTRIBUTES,
        # )
        # result = json.loads(c.response_to_json())["entries"][0]

        # group_name = result['attributes']['distinguishedName']
        # c.search(
        #     search_base=base_dn,
        #     search_filter=f"(cn={samaccountname})",
        #     attributes=ALL_ATTRIBUTES,
        # )
        # result = json.loads(c.response_to_json())["entries"][0]
        
        # account_name = result['attributes']['distinguishedName']

        c.modify(distinguished_groupname,{'member': [(MODIFY_DELETE, [distinguished_username])]})

        modify_result = c.result['description']
        final_result = {
            'action': 'Add user to Group',
            'result': modify_result,
            'group_name': distinguished_groupname,
            'user_name': distinguished_username
        }
        #print(str(final_result))
        return json.dumps(final_result)


if __name__ == "__main__":
    ActiveDirectory.run()
