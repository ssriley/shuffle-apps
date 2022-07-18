
import datetime
from logging import exception
import json
import traceback
import subprocess
import winrm
from winrm.protocol import Protocol

from walkoff_app_sdk.app_base import AppBase


class SS_WinRM(AppBase):
    """
    An example of a Walkoff App.
    Inherit from the AppBase class to have Redis, logging, and console
    logging set up behind the scenes.
    """

    __version__ = "1.0.0"
    app_name = (
        "SS - WinRM"  # this needs to match "name" in api.yaml for WALKOFF to work
    )

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)

    def krbauth(self,username, password, kerberos_config_file_id):
        try:
            #set_kerberos_file_path = ['/bin/sh','export KRB5_CONFIG=/tmp/krb5.conf']
            #subprocess.run(set_kerberos_file_path)
            krb5_file = self.get_file(kerberos_config_file_id)

            with open('/etc/krb5.conf', "wb+") as krb5:
                krb5.write(krb5_file["data"])

            cmd = ['kinit', username]
            success = subprocess.run(cmd, input=password.encode(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
            ticket_cache = subprocess.run('klist', capture_output=True)
            return {'ticket_cache': str(ticket_cache)}
            #return not bool(success)
        except Exception:
            my_error = {"kerberos_auth_result": traceback.format_exc()}
            return my_error

    def run_powershell_script(self,username, password, windows_host, powershell_script, auth_mode='ntlm', kerberos_config_file_id=None):
        if auth_mode == 'kerberos':
            try:
                ticket = self.krbauth(username,password, kerberos_config_file_id)
            except Exception:
                my_error = {"ticket_retrieve_result": traceback.format_exc()}
                return my_error
            if ticket:
                try:
                    s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                    remote_ps = s.run_ps(powershell_script)
                    result = {"status_code": str(remote_ps.status_code),
                            "result": remote_ps.std_out.decode('utf-8')
                            }
                    return result
                except Exception:
                    my_error = {"result": traceback.format_exc()}
                    return my_error
            else:
                return {'result': 'Did not Login Successfully'}
        else:
            try:
                s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                remote_ps = s.run_ps(powershell_script)
                result = {"status_code": str(remote_ps.status_code),
                        "result": remote_ps.std_out.decode('utf-8')
                        }
                return result
            except Exception:
                my_error = {"result": traceback.format_exc(),
                "krbauth_result": str(ticket)}
                return my_error

    def run_command_prompt(self,username, password, windows_host, command, command_args=None, auth_mode='ntlm', kerberos_config_file_id=None):
        if auth_mode == 'kerberos':
            try:
                ticket = self.krbauth(username,password, kerberos_config_file_id)
            except Exception:
                my_error = {"keberos_auth_result": traceback.format_exc()}
                return my_error
            if ticket:
                try:
                    if command_args:
                        command_args = command_args.replace("'", '"', -1)
                        command_args = json.loads(command_args)
                        s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                        remote_command = s.run_cmd(command, command_args)
                        result = {"status_code": str(remote_command.status_code),
                                "result": remote_command.std_out.decode('utf-8'),
                                "krbauth_result": str(ticket)
                                }
                        return result
                    else:
                        s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                        remote_command = s.run_cmd(command)
                        result = {"status_code": str(remote_command.status_code),
                                "result": remote_command.std_out.decode('utf-8'),
                                "krbauth_result": str(ticket)
                                }
                        return result
                except Exception:
                    my_error = {"result": traceback.format_exc(),
                                "krbauth_result": str(ticket)}
                    return my_error
            else:
                return {'result': 'Did not Login Successfully'}
        else:
            try:
                if command_args:
                    command_args = command_args.replace("'", '"', -1)
                    command_args = json.loads(command_args)
                    s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                    remote_command = s.run_cmd(command, command_args)
                    result = {"status_code": str(remote_command.status_code),
                            "result": remote_command.std_out.decode('utf-8'),
                            "krbauth_result": str(ticket)
                            }
                    return result
                else:
                    s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                    remote_command = s.run_cmd(command)
                    result = {"status_code": str(remote_command.status_code),
                            "result": remote_command.std_out('utf-8'),
                            "krbauth_result": str(ticket)
                            }
                    return result
            except Exception:
                my_error = {"result": traceback.format_exc()}
                return my_error
    
    def check_kerberos(self, username, password, kerberos_config_file_id):
        try:
            #set_kerberos_file_path = ['/bin/sh','export KRB5_CONFIG=/tmp/krb5.conf']
            #subprocess.run(set_kerberos_file_path)
            krb5_file = self.get_file(kerberos_config_file_id)

            with open('/etc/krb5.conf', "wb+") as krb5:
                krb5.write(krb5_file["data"])

            cmd = ['kinit', username]
            success = subprocess.run(cmd, input=password.encode(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
            ticket_cache = subprocess.run('klist', capture_output=True)
            return {'ticket_cache': str(ticket_cache)}
        except Exception:
            my_error = {"kerberos_auth_result": traceback.format_exc()}
            return my_error

    def run_powershell_file(self,username, password, windows_host, powershell_script_file_id=None, auth_mode='ntlm', kerberos_config_file_id=None):
        if auth_mode == 'kerberos':
            try:
                ticket = self.krbauth(username,password, kerberos_config_file_id)
            except Exception:
                my_error = {"ticket_retrieve_result": traceback.format_exc()}
                return my_error
            if ticket:
                try:
                    powershell_file = self.get_file(powershell_script_file_id)
                    ps_file_contents = powershell_file["data"].decode('utf-8')
                    ps = "Get-Process"
                    s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                    remote_ps = s.run_ps(str(powershell_file["data"]))
                    result = {"status_code": str(remote_ps.status_code),
                            "result": remote_ps.std_out.decode('utf-8'),
                            "script": ps_file_contents
                            }
                    return result
                except Exception:
                    my_error = {"result": traceback.format_exc()}
                    return my_error
            else:
                return {'result': 'Did not Login Successfully'}
        else:
            try:
                powershell_file = self.get_file(powershell_script_file_id)
                s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                remote_ps = s.run_ps(powershell_file["data"].decode('utf-8'))
                result = {"status_code": str(remote_ps.status_code),
                        "result": remote_ps.std_out.decode('utf-8')
                        }
                return result
            except Exception:
                my_error = {"result": traceback.format_exc(),
                "krbauth_result": str(ticket)}
                return my_error

if __name__ == "__main__":
    SS_WinRM.run()
