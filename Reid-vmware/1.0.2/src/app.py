
from walkoff_app_sdk.app_base import AppBase

import atexit
import pyVmomi
from pyVmomi import vim
from pyVim.task import WaitForTask
from pyVim.connect import SmartConnect, Disconnect
import requests
from pyVmomi import vmodl
import json

class VMwareTools(AppBase):
    __version__ = "1.0.0"
    app_name = (
        "Test VMware Tools"  # this needs to match "name" in api.yaml for WALKOFF to work
    )

    def __init__(self, redis, logger, console_logger=None):
        """
        Each app should have this __init__ to set up Redis and logging.
        :param redis:
        :param logger:
        :param console_logger:
        """
        super().__init__(redis, logger, console_logger)


    def test_vcenter_connection(self,host_ip,username,password,port,disableSslCertValidation=True):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        try:
            session_id = si.content.sessionManager.currentSession.key
            #print(str(session_id))
            result = {
                "Message": "success",
                "session_id": "current session id: {}".format(session_id)
             }
            return json.dumps(result)
        except vmodl.MethodFault as error:
            result = {
                "Error": error.msg
            }
            return json.dumps(result)

    def __connect(self,host_ip,username,password,port,disableSslCertValidation=True):
        """
        Determine the most preferred API version supported by the specified server,
        then connect to the specified server using that API version, login and return
        the service instance object.
        """

        service_instance = None

        # form a connection...
        try:
            if disableSslCertValidation:
                service_instance = SmartConnect(host=host_ip,
                                                user=username,
                                                pwd=password,
                                                port=port,
                                                disableSslCertValidation=disableSslCertValidation)
            else:
                service_instance = SmartConnect(host=host_ip,
                                                user=username,
                                                pwd=password,
                                                port=port)

            # doing this means you don't need to remember to disconnect your script/objects
            atexit.register(Disconnect, service_instance)
        except IOError as io_error:
            print(io_error)
            result = {
                "Error": io_error
            }
            return json.dumps(result)
        if not service_instance:
            raise SystemExit("Unable to connect to host with supplied credentials.")

        return service_instance


if __name__ == "__main__":
    VMwareTools.run()
