
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
from types import NoneType
class VMwareTools(AppBase):
    __version__ = "1.1.3"
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
            #print(io_error)
            result = {
                "Error": "Error in Connection ".format(io_error)
            }
            return json.dumps(result)
        if not service_instance:
            #raise SystemExit("Unable to connect to host with supplied credentials.")
            return json.dumps({"Error": "Unable to connect with credentials"})
        return service_instance

    def wait_for_tasks(self,si, tasks):
        """Given the service instance and tasks, it returns after all the
    tasks are complete
    """
        property_collector = si.content.propertyCollector
        task_list = [str(task) for task in tasks]
        # Create filter
        obj_specs = [vmodl.query.PropertyCollector.ObjectSpec(obj=task)
                    for task in tasks]
        property_spec = vmodl.query.PropertyCollector.PropertySpec(type=vim.Task,
                                                                pathSet=[],
                                                                all=True)
        filter_spec = vmodl.query.PropertyCollector.FilterSpec()
        filter_spec.objectSet = obj_specs
        filter_spec.propSet = [property_spec]
        pcfilter = property_collector.CreateFilter(filter_spec, True)
        try:
            version, state = None, None
            # Loop looking for updates till the state moves to a completed state.
            while task_list:
                update = property_collector.WaitForUpdates(version)
                for filter_set in update.filterSet:
                    for obj_set in filter_set.objectSet:
                        task = obj_set.obj
                        for change in obj_set.changeSet:
                            if change.name == 'info':
                                state = change.val.state
                            elif change.name == 'info.state':
                                state = change.val
                            else:
                                continue

                            if not str(task) in task_list:
                                continue

                            if state == vim.TaskInfo.State.success:
                                # Remove task from taskList
                                task_list.remove(str(task))
                            elif state == vim.TaskInfo.State.error:
                                raise task.info.error
                # Move to next version
                version = update.version
        finally:
            if pcfilter:
                pcfilter.Destroy()

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
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
            cdrom = None
            for dev in vm.config.hardware.device:
                if isinstance(dev, vim.vm.device.VirtualIDEController):
                    if len(dev.device) < 2:
                        controller = dev
            cdrom_operation = vim.vm.device.VirtualDeviceSpec.Operation
            device_spec = vim.vm.device.VirtualDeviceSpec()
            connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            connectable.allowGuestControl = True
            connectable.startConnected = True

            cdrom = vim.vm.device.VirtualCdrom()
            cdrom.controllerKey = controller.key
            cdrom.key = -1
            cdrom.connectable = connectable
            cdrom.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo()
            #cdrom.backing = vim.vm.device.VirtualCdrom.IsoBackingInfo(fileName=iso)
            device_spec.operation = cdrom_operation.add
            device_spec.device = cdrom
            config_spec = vim.vm.ConfigSpec(deviceChange=[device_spec])
            WaitForTask(vm.Reconfigure(config_spec))
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
            task = vm.CreateSnapshot_Task(name=snap_name,description=snap_description,memory=bool(snap_memory == "True"),quiesce=bool(snap_quiesce == "True"))
            WaitForTask(task)
            return json.dumps({"Status": "Created snapshot for {0}".format(vm.name),
            "Task": "Result of task ".format(task.info.result)})
        except Exception as err:
            raise Exception(json.dumps({"Error was {0}".format(err)}))

    def add_disk(self,host_ip,username,password,port,disableSslCertValidation=True,vm_name=None, disk_size=1024, disk_type="thin"):
        """
        Add disk to vm
        """
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
        spec = vim.vm.ConfigSpec()
        # get all disks on a VM, set unit_number to the next available
        unit_number = 0
        controller = None
        for device in vm.config.hardware.device:
            if hasattr(device.backing, 'fileName'):
                unit_number = int(device.unitNumber) + 1
                # unit_number 7 reserved for scsi controller
                if unit_number == 7:
                    unit_number += 1
                if unit_number >= 16:
                    print("we don't support this many disks")
                    return -1
            if isinstance(device, vim.vm.device.VirtualSCSIController):
                controller = device
        if controller is None:
            print("Disk SCSI controller not found!")
            return -1
        # add disk here
        dev_changes = []
        new_disk_kb = int(disk_size) * 1024 * 1024
        disk_spec = vim.vm.device.VirtualDeviceSpec()
        disk_spec.fileOperation = "create"
        disk_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
        disk_spec.device = vim.vm.device.VirtualDisk()
        disk_spec.device.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()
        if disk_type == 'thin':
            disk_spec.device.backing.thinProvisioned = True
        disk_spec.device.backing.diskMode = 'persistent'
        disk_spec.device.unitNumber = unit_number
        disk_spec.device.capacityInKB = new_disk_kb
        disk_spec.device.controllerKey = controller.key
        dev_changes.append(disk_spec)
        spec.deviceChange = dev_changes
        WaitForTask(vm.ReconfigVM_Task(spec=spec))
        print("%sGB disk added to %s" % (disk_size, vm.config.name))
        return json.dumps({"Status": "Complete"})

    def delete_vm(self,host_ip,username,password,port,disableSslCertValidation=True,vm_dns_name=None, vm_ip=None,vm_name=None):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        vm = None
        if vm_dns_name:
            vm = si.content.searchIndex.FindByDnsName(None, vm_dns_name, True)
        elif vm_ip:
            vm = si.content.searchIndex.FindByIp(None, vm_ip, True)
        elif vm_name:
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
            #uuid = vm.summary.config.uuid
            #return json.dumps({"uuid": uuid})
            #vm = si.content.searchIndex.FindByUuid(None, uuid, True, False)
        if vm is None:
            result = {
                "Error": "Cannot find VM"
            }
            return json.dumps(result)
        if format(vm.runtime.powerState) == "poweredOn":
            TASK = vm.PowerOffVM_Task()
            #tasks.wait_for_tasks(si, [TASK])
            WaitForTask(TASK)
        TASK = vm.Destroy_Task()
        WaitForTask(TASK)
        return json.dumps({"Status": "Deleted vm ".format(vm.name)})

    def add_nic(self,host_ip,username,password,port,disableSslCertValidation=True,vm_dns_name=None, vm_ip=None,vm_name=None,network_name=None, nic_description="", nic_connect_on_start=True,nic_connected=False):
        si = self.__connect(host_ip=host_ip,username=username,password=password,port=port,disableSslCertValidation=disableSslCertValidation)
        vm = None
        if vm_dns_name:
            vm = si.content.searchIndex.FindByDnsName(None, vm_dns_name, True)
        elif vm_ip:
            vm = si.content.searchIndex.FindByIp(None, vm_ip, True)
        elif vm_name:
            content = si.RetrieveContent()
            vm = self.get_obj(content, [vim.VirtualMachine], vm_name)
        try:
            spec = vim.vm.ConfigSpec()
            nic_changes = []

            nic_spec = vim.vm.device.VirtualDeviceSpec()
            nic_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add

            nic_spec.device = vim.vm.device.VirtualVmxnet3()

            nic_spec.device.deviceInfo = vim.Description()
            nic_spec.device.deviceInfo.summary = nic_description
            nic_spec.device.deviceInfo.label = "Network Adapter 10"
            net_content = si.RetrieveContent()
            network = self.get_obj(net_content, [vim.Network], network_name)
            #return json.dumps({"network": network.name})
            
            # if isinstance(network, vim.OpaqueNetwork):
            #     nic_spec.device.backing = \
            #         vim.vm.device.VirtualEthernetCard.OpaqueNetworkBackingInfo()
            #     nic_spec.device.backing.opaqueNetworkType = \
            #         network.summary.opaqueNetworkType
            #     nic_spec.device.backing.opaqueNetworkId = \
            #         network.summary.opaqueNetworkId
            #else:
            nic_spec.device.backing = vim.vm.device.VirtualEthernetCard.NetworkBackingInfo()
            nic_spec.device.backing.useAutoDetect = False
            #nic_spec.device.backing.network = network
            nic_spec.device.backing.deviceName = network.name
            nic_spec.device.key = 4000
            nic_spec.device.deviceInfo.label = "Network Adapter 10"
            nic_spec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
            nic_spec.device.connectable.startConnected = bool(nic_connect_on_start == "True")
            nic_spec.device.connectable.allowGuestControl = True
            nic_spec.device.connectable.connected = bool(nic_connected == "True")
            nic_spec.device.connectable.status = 'untried'
            nic_spec.device.wakeOnLanEnabled = True
            nic_spec.device.addressType = 'assigned'

            nic_changes.append(nic_spec)
            spec.deviceChange = nic_changes
            WaitForTask(vm.ReconfigVM_Task(spec=spec))
            return json.dumps({"Status": "Added Nic Card to Port Group {0}".format(network_name)})
        except vmodl.MethodFault as error:
            return json.dumps({"Error": "Error {0}".format(error.msg)})
        except vmodl.RuntimeFault as rt:
            return json.dumps({"Error": "Error {0}".format(rt.msg)})
if __name__ == "__main__":
    VMwareTools.run()
