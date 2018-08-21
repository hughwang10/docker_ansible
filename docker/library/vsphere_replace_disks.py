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
module: vsphere_replace_disks
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

    datastores:
        required: true
        description:
            - List Vsphere datastore

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
            disk_folder=dict(required=True, type='str'),
            disk_start_id=dict(required=True, type='str'),
            vm_name=dict(required=True, type='str'),
            vcenter=dict(required=True, type='str'),
            vcusername=dict(required=True, type='str'),
            vcpassword=dict(required=True, type='str'),
            datacenter=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            datastores=dict(required=True, type='list'),
            disk_sizes=dict(required=True, type='list'),
            esxihostname=dict(required=True, type='str'),
            folder_name=dict(default="", type='str'),
        ),
        supports_check_mode=True
    )
    try:
        si = None
        vsphere_vcenter = module.params.get('vcenter')
        vsphere_vcusername = module.params.get('vcusername')
        vsphere_vcpassword = module.params.get('vcpassword')
        vsphere_datacenter = module.params.get('datacenter', None)
        vsphere_datastore = module.params.get('datastore')
        vsphere_esxihostname = module.params.get('esxihostname')
        disk_folder = module.params.get('disk_folder')
        disk_start_id = module.params.get('disk_start_id')
        datastores = module.params.get('datastores')
#        datastores = []
        disk_sizes = module.params.get('disk_sizes')
        vm_name = module.params.get('vm_name')
        folder_name = module.params.get('folder_name')
        added_disks = []
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
#        datastores.append("datastore2")
#        datastores.append("datastore1")

#        datacenter = module.params.get('datacenter', None)
        dc = [entity for entity in content.rootFolder.childEntity
                        if hasattr(entity, 'vmFolder') and entity.name == vsphere_datacenter][0]


        search = content.searchIndex
        vm = search.FindByInventoryPath( vsphere_datacenter + '/vm/' + folder_name + '/' + vm_name )
#        vm = search.FindByInventoryPath( vsphere_datacenter + '/vm/root-v1/ts-01-v1' )
        if vm == None:
          vm = search.FindByDatastorePath(dc, '[' + vsphere_datastore + '] ' + vm_name + '/' + vm_name + '.vmx')

        controller = None
        devices = vm.config.hardware.device
        for device in devices:
            if isinstance(device, vim.vm.device.VirtualSCSIController):
                controller = device

#        vmconf = vim.vm.ConfigSpec()
        
        disk_size_index = 0
        for disk_datastore, disk_id in zip(datastores,  range(int(disk_start_id), int(disk_start_id) + len(datastores))):
          disk1 = FindSCSIDisk(0, int(disk_id), vm)
          if disk1 != None:
             RemoveDevice(vm, disk1)

          disk_path = '[' + disk_datastore + '] ' + disk_folder + '/' + vm_name + '_' + str(disk_id) + '.vmdk'
          added_disks.append(disk_path)
          virtual_disk = vim.vm.device.VirtualDisk()

          virtual_disk.backing = vim.vm.device.VirtualDisk.FlatVer2BackingInfo()

          virtual_disk.backing.diskMode = vim.vm.device.VirtualDiskOption.DiskMode.independent_persistent


          virtual_disk.backing.thinProvisioned = True
          virtual_disk.backing.eagerlyScrub = False
          virtual_disk.backing.fileName = disk_path

#          virtual_disk.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
#          virtual_disk.connectable.startConnected = True
#          virtual_disk.connectable.allowGuestControl = False
#          virtual_disk.connectable.connected = True
          virtual_disk.capacityInKB = 1024 * 1024 * (int(disk_sizes[disk_size_index]))

          virtual_disk.key = -100
          virtual_disk.controllerKey = controller.key
          virtual_disk.unitNumber = int(disk_id)

          device_spec = vim.vm.device.VirtualDiskSpec()
          device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
          device_spec.device = virtual_disk
          device_spec.fileOperation = "create"

          vmconf = vim.vm.ConfigSpec()
          vmconf.deviceChange.append(device_spec)
          disk_size_index = disk_size_index + 1
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

