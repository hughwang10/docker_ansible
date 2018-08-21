#!/usr/bin/env python
# Copyright (C) 2015 by
# Ericsson AB
# S-164 83 Stockholm
# Sweden
# Tel: +46 10 719 00 00
#
# The program may be used and/or copied only with the written permission
# from Ericsson AB, or in accordance with the terms and
# conditions stipulated in the agreement/contract under which the program
# has been supplied.
#
# All rights reserved.

DOCUMENTATION = '''
---
module: vsphere_attach_disks
author: MSP Cloud Platform
version_added: "0.0.1"
short_description: Load file to VMWare datastore
requirements: [ pyshpere, pyVmomi ]
description:
    - Load a file to vmware datastore
options:
    disk_file_paths:
        required: true
        description:
            - List of paths and name to .vmdk file to mount.
    
    disk_ids:
        required: true
        description:
            - List of scsi addresses where to mount.

    vcenter:
        required: true
        description:
            - Vsphere vcenter

    vcusername:
        required: true
        description:
            - Vsphere vcusername

    vcpassword:
        required: true
        description:
            - Vsphere vcpassword

    datacenter:
        required: true
        description:
            - Vsphere datacenter

    datastore:
        required: true
        description:
            - Vsphere datastore

    esxihostname:
        required: true
        description:
            - Vsphere esxi hostname

'''

import atexit
import time

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect
from pyVim.task import WaitForTask

import time

def FindSCSIDisk(controller, unit, vm):
    ret_device = None
    for device in vm.config.hardware.device: 
       if isinstance(device, vim.vm.device.VirtualDisk):
         if (device.unitNumber == unit and (controller+1000) == device.controllerKey): 
           ret_device = device
           break
    return ret_device

def RemoveDevice(vm1, device, fileop = None):
   # Helper to do the removal of a single device.
   cspec = vim.vm.ConfigSpec()
   cspec = RemoveDeviceFromSpec(cspec, device)
   WaitForTask(vm1.Reconfigure(cspec))
   return vm1

def RemoveDeviceFromSpec(cspec, device, fileop = None):
   """ Remove the specified device from the vm """
   devSpec = vim.vm.device.VirtualDeviceSpec()
   devSpec.device = device
   devSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove

   devSpec.fileOperation = vim.vm.device.VirtualDeviceSpec.FileOperation.destroy 

   my_deviceChange = cspec.deviceChange
   my_deviceChange.append(devSpec) 

   cspec.deviceChange = my_deviceChange
   return cspec

def main():
    module = AnsibleModule(
        argument_spec = dict(
            disk_file_paths=dict(required=True, type='list'),
            disk_ids=dict(required=True, type='list'),
            vm_name=dict(required=True, type='str'),
            vcenter=dict(required=True, type='str'),
            vcusername=dict(required=True, type='str'),
            vcpassword=dict(required=True, type='str'),
            datacenter=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            esxihostname=dict(required=True, type='str'),
            folder_name=dict(default="", type='str'),
        ),
        supports_check_mode=True
    )
    try:
        si = None
        vsphere_vcenter = module.params.get('vcenter')
        vsphere_vcusername = module.params.get('vcusername').replace("##at##","@")
        vsphere_vcpassword = module.params.get('vcpassword')
        vsphere_datacenter = module.params.get('datacenter')
        vsphere_datastore = module.params.get('datastore')
        vsphere_esxihostname = module.params.get('esxihostname')
        disk_paths = module.params.get('disk_file_paths')
        disk_ids = module.params.get('disk_ids')
        vm_name = module.params.get('vm_name')
        folder_name = module.params.get('folder_name')
        try:
            si = connect.SmartConnect(host=vsphere_vcenter,
                                                    user=vsphere_vcusername,
                                                    pwd=vsphere_vcpassword,
                                                    port=int(443))
        except IOError as e:
            pass
        if not si:
            raise SystemExit(-1)

        # Ensure that we cleanly disconnect in case our code dies
        atexit.register(connect.Disconnect, si)

        content = si.RetrieveContent()


        datacenter = module.params.get('datacenter', None)
        dc = [entity for entity in content.rootFolder.childEntity
                        if hasattr(entity, 'vmFolder') and entity.name == datacenter][0]


        search = content.searchIndex
        vm = search.FindByInventoryPath( vsphere_datacenter + '/vm/' + folder_name + '/' + vm_name )
        if vm == None:
          vm = search.FindByDatastorePath(dc, '[' + vsphere_datastore + '] ' + vm_name + '/' + vm_name + '.vmx')

        for disk_number1 in disk_ids:
#          print('[' + vsphere_datastore + '] ' + vm_name + '/' + vm_name + '.vmx')
          disk1 = FindSCSIDisk(0, int(disk_number1), vm)
#          print('[' + vsphere_datastore + '] ' + vm_name + '/' + vm_name + '.vmx')
          if disk1 != None:
             RemoveDevice(vm, disk1)

        # the details we will need to make the disk:
#        disk_path = '[' + vsphere_datastore + '] ' + disk_path
        controller = None
        devices = vm.config.hardware.device
        for device in devices:
            if isinstance(device, vim.vm.device.VirtualSCSIController):
                controller = device
        vmconf = vim.vm.ConfigSpec()
        for disk_number, file_path in zip(disk_ids, disk_paths):
          disk_path = '[' + vsphere_datastore + '] ' + file_path
#          print(str(disk_number) + ": " + disk_path)
          virtual_disk = vim.vm.device.VirtualDisk()

        # https://github.com/vmware/pyvmomi/blob/master
        # /docs/vim/vm/device/VirtualDisk/FlatVer2BackingInfo.rst
          virtual_disk.backing = \
            vim.vm.device.VirtualDisk.FlatVer2BackingInfo()

        # https://github.com/vmware/pyvmomi/blob/master
        # /docs/vim/vm/device/VirtualDiskOption/
        # DiskMode.rst#independent_persistent
          virtual_disk.backing.diskMode = \
              vim.vm.device.VirtualDiskOption.DiskMode.persistent

          virtual_disk.backing.thinProvisioned = True
          virtual_disk.backing.eagerlyScrub = False
          virtual_disk.backing.fileName = disk_path

          virtual_disk.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
          virtual_disk.connectable.startConnected = True
          virtual_disk.connectable.allowGuestControl = False
          virtual_disk.connectable.connected = True

          virtual_disk.key = -100
          virtual_disk.controllerKey = controller.key
          virtual_disk.unitNumber = int(disk_number)

          device_spec = vim.vm.device.VirtualDiskSpec()
          device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
          device_spec.device = virtual_disk

          vmconf.deviceChange.append(device_spec)

        WaitForTask(vm.ReconfigVM_Task(vmconf))

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        raise SystemExit(-1)
    except Exception, e:
        print "Caught exception: %s" % str(e)
        raise SystemExit(-1)
    rc = None
    out = ''
    err = ''
    result = {}
    result['disk_file_path'] = "OK"
    result['vm_name'] = "OK"


    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

# Start program
if __name__ == "__main__":
    main()

