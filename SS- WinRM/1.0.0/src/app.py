
import datetime
from logging import exception
import json
import traceback
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

    def run_powershell_script(self,username, password, windows_host, powershell_script, auth_mode='ntlm'):
        try:
            s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
            remote_ps = s.run_ps(powershell_script)
            result = {"status_code": remote_ps.status_code,
                    "result": remote_ps.std_out
                    }
            return result
        except exception:
            my_error = {"result": traceback.format_exc()}
            return my_error

    def run_command_prompt(self,username, password, windows_host, command, command_args=None, auth_mode='ntlm'):
        try:
            if command_args:
                command_args = command_args.replace("'", '"', -1)
                command_args = json.loads(command_args)
                s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                remote_command = s.run_cmd(command, command_args)
                result = {"status_code": remote_command.status_code,
                        "result": remote_command.std_out
                        }
                return result
            else:
                s = winrm.Session(windows_host, auth=(username, password), server_cert_validation='ignore', transport=auth_mode)
                remote_command = s.run_cmd(command)
                result = {"status_code": remote_command.status_code,
                        "result": remote_command.std_out
                        }
                return result
        except exception:
            my_error = {"result": traceback.format_exc()}
            return my_error

if __name__ == "__main__":
    SS_WinRM.run()
