
from types import NoneType
from walkoff_app_sdk.app_base import AppBase
import sys
import atexit
import pyVmomi
from pyVmomi import vim
from pyVim.task import WaitForTask
from pyVim.connect import SmartConnect, Disconnect
import requests
from pyVmomi import vmodl
import json

class VMwareTools(AppBase):
    __version__ = "1.0.8"
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
            #raise SystemExit("Unable to connect to host with supplied credentials.")
            return json.dumps({"Error": "Unable to connect with credentials"})
        return service_instance

    def collect_properties(self, si, view_ref, obj_type, path_set=None,
                       include_mors=False):
        """
        Collect properties for managed objects from a view ref
        Check the vSphere API documentation for example on retrieving
        object properties:
            - http://goo.gl/erbFDz
        Args:
            si          (ServiceInstance): ServiceInstance connection
            view_ref (pyVmomi.vim.view.*): Starting point of inventory navigation
            obj_type      (pyVmomi.vim.*): Type of managed object
            path_set               (list): List of properties to retrieve
            include_mors           (bool): If True include the managed objects
                                        refs in the result
        Returns:
            A list of properties for the managed objects
        """
        collector = si.content.propertyCollector

        # Create object specification to define the starting point of
        # inventory navigation
        obj_spec = pyVmomi.vmodl.query.PropertyCollector.ObjectSpec()
        obj_spec.obj = view_ref
        obj_spec.skip = True

        # Create a traversal specification to identify the path for collection
        traversal_spec = pyVmomi.vmodl.query.PropertyCollector.TraversalSpec()
        traversal_spec.name = 'traverseEntities'
        traversal_spec.path = 'view'
        traversal_spec.skip = False
        traversal_spec.type = view_ref.__class__
        obj_spec.selectSet = [traversal_spec]

        # Identify the properties to the retrieved
        property_spec = pyVmomi.vmodl.query.PropertyCollector.PropertySpec()
        property_spec.type = obj_type

        if not path_set:
            property_spec.all = True

        property_spec.pathSet = path_set

        # Add the object and property specification to the
        # property filter specification
        filter_spec = pyVmomi.vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = [obj_spec]
        filter_spec.propSet = [property_spec]

        # Retrieve properties
        props = collector.RetrieveContents([filter_spec])

        data = []
        for obj in props:
            properties = {}
            for prop in obj.propSet:
                properties[prop.name] = prop.val

            if include_mors:
                properties['obj'] = obj.obj

            data.append(properties)
        return data


    def get_container_view(self, si, obj_type, container=None):
        """
        Get a vSphere Container View reference to all objects of type 'obj_type'
        It is up to the caller to take care of destroying the View when no longer
        needed.
        Args:
            obj_type (list): A list of managed object types
        Returns:
            A container view ref to the discovered managed objects
        """
        if not container:
            container = si.content.rootFolder

        view_ref = si.content.viewManager.CreateContainerView(
            container=container,
            type=obj_type,
            recursive=True
        )
        return view_ref


    def search_for_obj(self, content, vim_type, name, folder=None, recurse=True):
        """
        Search the managed object for the name and type specified
        Sample Usage:
        get_obj(content, [vim.Datastore], "Datastore Name")
        """
        if folder is None:
            folder = content.rootFolder

        obj = None
        container = content.viewManager.CreateContainerView(folder, vim_type, recurse)

        for managed_object_ref in container.view:
            if managed_object_ref.name == name:
                obj = managed_object_ref
                break
        container.Destroy()
        return obj


    def get_all_obj(self, content, vim_type, folder=None, recurse=True):
        """
        Search the managed object for the name and type specified
        Sample Usage:
        get_obj(content, [vim.Datastore], "Datastore Name")
        """
        if not folder:
            folder = content.rootFolder

        obj = {}
        container = content.viewManager.CreateContainerView(folder, vim_type, recurse)

        for managed_object_ref in container.view:
            obj[managed_object_ref] = managed_object_ref.name

        container.Destroy()
        return obj


    def get_obj(self, content, vim_type, name, folder=None, recurse=True):
        """
        Retrieves the managed object for the name and type specified
        Throws an exception if of not found.
        Sample Usage:
        get_obj(content, [vim.Datastore], "Datastore Name")
        """
        obj = self.search_for_obj(content, vim_type, name, folder, recurse)
        if not obj:
            #raise RuntimeError("Managed Object " + name + " not found.")
            return json.dumps({"Error": "Managed Object Not Found " + name})
        return obj

    def list_snapshots_recursively(self,snapshots):
        snapshot_data = []
        for snapshot in snapshots:
            snap_text = "Name: %s; Description: %s; CreateTime: %s; State: %s" % (
                                            snapshot.name, snapshot.description,
                                            snapshot.createTime, snapshot.state)
            snapshot_data.append(snap_text)
            snapshot_data = snapshot_data + self.list_snapshots_recursively(
                                            snapshot.childSnapshotList)
        return snapshot_data

    def reboot_vm(self,host_ip,username,password,port,disableSslCertValidation=True,vm_ip=None,vm_name=None):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        vm = None
        if vm_ip:
            vm = si.content.searchIndex.FindByIp(None, vm_ip, True)
        elif vm_name:
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
        
        if vm is None:
            result = {
                "Error": "Cannot find VM"
            }
            return json.dumps(result)
        WaitForTask(vm.ResetVM_Task())
        result = {
            "Search": "Found: {0}".format(vm.name),
            "Current_State": "The current powerState is: {0}".format(vm.runtime.powerState),
            "Complete": "Reboot completed"
        }
        return json.dumps(result)

    def power_on_vm(self,host_ip,username,password,port,disableSslCertValidation=True,vm_name=None):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        vm = None

        if vm_name:
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
        
        if vm is None:
            result = {
                "Error": "Cannot find VM"
            }
            return json.dumps(result)

        task = vm.PowerOn()
        #self.wait_for_tasks(si,task)
        WaitForTask(task)
        result = {
            "search": "Found: {0}".format(vm.name),
            "current_state": "The current powerState is: {0}".format(vm.runtime.powerState),
            "task_result": task.info.result
        }
        return json.dumps(result)

    def create_vm(self,
    host_ip, 
    username,
    password,
    port,
    vm_name, 
    datacenter_name, 
    esxi_host_ip,
    disableSslCertValidation=True,
    datastore_name=None,
    memory=4,
    guest="otherGuest",
    annotation="Example",
    cpus=1
    ):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        content = si.RetrieveContent()
        destination_host = self.get_obj(content, [vim.HostSystem], esxi_host_ip)
        source_pool = destination_host.parent.resourcePool
        if datastore_name is None:
            datastore_name = destination_host.datastore[0].name

        config = vim.vm.ConfigSpec()
        config.annotation = annotation
        config.memoryMB = int(memory)
        config.guestId = guest
        config.name = vm_name
        config.numCPUs = int(cpus)
        files = vim.vm.FileInfo()
        files.vmPathName = "["+datastore_name+"]"
        config.files = files

        for child in content.rootFolder.childEntity:
            if child.name == datacenter_name:
                vm_folder = child.vmFolder  # child is a datacenter
                break
        else:
            #print("Datacenter %s not found!" % datacenter_name)
            result = {
                "Datacenter Not Found": datacenter_name
            }
            return json.dumps(result)
            #sys.exit(1)

        try:
            WaitForTask(vm_folder.CreateVm(config, pool=source_pool, host=destination_host))
            #print("VM created: %s" % vm_name)
            result = {
                "VM_Created": vm_name
            }
            return json.dumps(result)
        except vim.fault.DuplicateName:
            #print("VM duplicate name: %s" % vm_name, file=sys.stderr)
            result = {
                "Vm_Duplicate_Name": vm_name
            }
            return json.dumps(result)
        except vim.fault.AlreadyExists:
            #print("VM name %s already exists." % vm_name, file=sys.stderr)
            result = {
                "VM_name_already_exists": vm_name
            }
            return json.dumps(result)
    def list_snapshots(self,host_ip,username,password,port,disableSslCertValidation=True,vm_ip=None, vm_name=None):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        vm = None
        if vm_ip:
            vm = si.content.searchIndex.FindByIp(None, vm_ip, True)
        elif vm_name:
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
        if vm is None:
            result = {
                "Error": "Cannot find VM"
            }
            return json.dumps(result)
        snap_list = []
        try:
            snapshot_paths = self.list_snapshots_recursively(vm.snapshot.rootSnapshotList)

            for snapshot in snapshot_paths:
                snap_list.append(snapshot)
            result = {
                "Snapshots": "Found: {0}".format(snap_list)
            }
            return json.dumps(result)
        except NoneType as error:
            return json.dumps({"Status": "No Snapshots Found"})

    def create_snapshot(self,host_ip,username,password,port,disableSslCertValidation=True,vm_ip=None, vm_name=None,snap_name="Test",snap_description="TEST TEST", snap_memory=False,snap_quiesce=False):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        vm = None
        if vm_ip:
            vm = si.content.searchIndex.FindByIp(None, vm_ip, True)
        elif vm_name:
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
        if vm is None:
            result = {
                "Error": "Cannot find VM"
            }
            return json.dumps(result)
        try:
            task = vm.CreateSnapshotEx_Task(name=snap_name,description=snap_description,memory=snap_memory)
            WaitForTask(task)
            return json.dumps({"Status": "Created snapshot for {0}".format(vm.name),
            "Task": "Result of task ".format(task.info.result)})
        except:
            return json.dumps({"Status": "Something went wrong."})
if __name__ == "__main__":
    VMwareTools.run()
