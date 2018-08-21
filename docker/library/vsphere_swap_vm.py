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
module: vsphere_swap_vm
author: MSP Cloud Platform
version_added: "0.0.1"
short_description: Update vm config
requirements: [ pyshpere, pyVmomi ]
description:
    - Load a file to vmware datastore
options:
    poweroff_mode:
        required: false
        description:
            - hard or soft.

    vm_name_new:
        required: true
        description:
            - hard or soft.

    vm_name_old:
        required: true
        description:
            - hard or soft.

    folder_name_new:
        required: false
        description:
            - hard or soft.

    folder_name_old:
        required: false
        description:
            - hard or soft.

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
    for device in vm.config.hardware.device: 
       if isinstance(device, vim.vm.device.VirtualDisk):
         if (device.unitNumber == unit and (controller+1000) == device.controllerKey): 
           return device

def RemoveDevice(vm1, device, fileop = None):
   # Helper to do the removal of a single device.
   cspec = vim.vm.ConfigSpec()
   cspec = RemoveDeviceFromSpec(cspec, device, fileop)
   WaitForTask(vm1.Reconfigure(cspec))
   return vm1

def RemoveDeviceFromSpec(cspec, device, fileop = None):
   """ Remove the specified device from the vm """
   devSpec = vim.vm.device.VirtualDeviceSpec()
   devSpec.device = device
   devSpec.operation = vim.vm.device.VirtualDeviceSpec.Operation.remove

   devSpec.fileOperation = fileop

   my_deviceChange = cspec.deviceChange
   my_deviceChange.append(devSpec) 
   cspec.deviceChange = my_deviceChange
   
   return cspec

def ConnectStateAllNics(vm, state):
    vmconf = vim.vm.ConfigSpec()
    for device in vm.config.hardware.device: 
       if isinstance(device, vim.vm.device.VirtualVmxnet3):
          devspec = vim.vm.device.VirtualDeviceSpec()
          devspec.operation = vim.vm.device.VirtualDeviceSpec.Operation.edit
          devspec.device = device
          devspec.device.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
          devspec.device.connectable.startConnected = state
          devspec.device.connectable.allowGuestControl = False
          devspec.device.connectable.connected = state
          vmconf.deviceChange.append(devspec)
    return vmconf

def wait_for_tools(vm):
    """
    Waits until vmware tools up and running
    """
    count = 0
#    if hasattr(vm.guest, 'toolsRunningStatus'):
    while vm.guest.toolsRunningStatus != vim.GuestInfo.ToolsRunningStatus.guestToolsRunning and count < 90:
        time.sleep(1)
        count = count + 1

    return

def move_disks(vmnew, vmold, si):
        disk_ids = []
        disk_files = []
        disks = False
        for disk_number1 in [ 1,2,3,4,5 ]:
          disk1 = FindSCSIDisk(0, disk_number1, vmold)
          if disk1 != None:
            one_file = re.search('(.*)$', disk1.backing.fileName)
            if disk1.backing.diskMode == vim.vm.device.VirtualDiskOption.DiskMode.independent_persistent:
              disk_files.append(one_file.group(1))
              disk_ids.append(disk_number1)
              RemoveDevice(vmold, disk1, None)
              disks = True
        vmconf = vim.vm.ConfigSpec()
        if not disks:
          return
        for disk_number2, disk2_path in zip(disk_ids, disk_files):
        # the details we will need to connect the disk:
          disk2 = FindSCSIDisk(0, disk_number2, vmnew)
          if disk2 != None:
              RemoveDevice(vmnew, disk2, None)
#          disk_fullpath = '[' + vsphere_datastore + '] ' + disk2_path
          disk_fullpath = disk2_path
          controller = None
          devices = vmnew.config.hardware.device
          for device in devices:
              if isinstance(device, vim.vm.device.VirtualSCSIController):
                  controller = device

          virtual_disk = vim.vm.device.VirtualDisk()

        # https://github.com/vmware/pyvmomi/blob/master
        # /docs/vim/vm/device/VirtualDisk/FlatVer2BackingInfo.rst
          virtual_disk.backing = \
              vim.vm.device.VirtualDisk.FlatVer2BackingInfo()

        # https://github.com/vmware/pyvmomi/blob/master
        # /docs/vim/vm/device/VirtualDiskOption/
        # DiskMode.rst#independent_persistent
          virtual_disk.backing.diskMode = \
              vim.vm.device.VirtualDiskOption.DiskMode.independent_persistent

          virtual_disk.backing.thinProvisioned = True
          virtual_disk.backing.eagerlyScrub = False
          virtual_disk.backing.fileName = disk_fullpath

          virtual_disk.connectable = vim.vm.device.VirtualDevice.ConnectInfo()
          virtual_disk.connectable.startConnected = True
          virtual_disk.connectable.allowGuestControl = False
          virtual_disk.connectable.connected = True

          virtual_disk.key = -100
          virtual_disk.controllerKey = controller.key
          virtual_disk.unitNumber = disk_number2

          device_spec = vim.vm.device.VirtualDiskSpec()
          device_spec.operation = vim.vm.device.VirtualDeviceSpec.Operation.add
          device_spec.device = virtual_disk

          vmconf.deviceChange.append(device_spec)

        WaitForTask(vmnew.ReconfigVM_Task(vmconf))
        return

def main():
    module = AnsibleModule(
        argument_spec = dict(
            poweroff_mode=dict(required=False, choices=['hard', 'soft'], type='str', default='soft'),
            vm_name_new=dict(required=True, type='str'),
            vm_name_old=dict(required=True, type='str'),
            poweron_delay=dict(default=5, type='str'),
            vcenter=dict(required=True, type='str'),
            vcusername=dict(required=True, type='str'),
            vcpassword=dict(required=True, type='str'),
            datacenter=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            esxihostname=dict(required=True, type='str'),
            folder_name_new=dict(default="", type='str'),
            folder_name_old=dict(default="", type='str'),
        ),
        supports_check_mode=True
    )
    old_changed = False
    new_changed = False
    connectstate = True
    vm = None
    vm2 = None
    try:
        si = None
        vsphere_vcenter = module.params.get('vcenter')
        vsphere_vcusername = module.params.get('vcusername').replace("##at##","@")
        vsphere_vcpassword = module.params.get('vcpassword')
        vsphere_datacenter = module.params.get('datacenter')
        vsphere_datastore = module.params.get('datastore')
        vsphere_esxihostname = module.params.get('esxihostname')
        poweroff_mode = module.params.get('poweroff_mode')
        vm_new = module.params.get('vm_name_new')
        vm_old = module.params.get('vm_name_old')
        folder_new = module.params.get('folder_name_new')
        folder_old = module.params.get('folder_name_old')
        poweron_delay = module.params.get('poweron_delay')
        try:
            si = connect.SmartConnect(host=vsphere_vcenter,
                                                    user=vsphere_vcusername,
                                                    pwd=vsphere_vcpassword,
                                                    port=int(443))
        except IOError as e:
            pass
        if not si:
            print("Could not connect to the specified host using specified "
                  "username and password")
            raise SystemExit(-1)

        # Ensure that we cleanly disconnect in case our code dies
        atexit.register(connect.Disconnect, si)

        content = si.RetrieveContent()

#        datacenter = module.params.get('datacenter', None)
        dc = [entity for entity in content.rootFolder.childEntity
                        if hasattr(entity, 'vmFolder') and entity.name == vsphere_datacenter][0]

        search = content.searchIndex
        vm = search.FindByInventoryPath( vsphere_datacenter + '/vm/' + folder_old + '/' + vm_old )
        if vm == None:
          vm = search.FindByDatastorePath(dc, '[' + vsphere_datastore + '] ' + vm_old + '/' + vm_old + '.vmx')
        if vm != None:
          if (hasattr(vm, 'runtime') and vm.runtime.powerState == vim.VirtualMachinePowerState.poweredOn):
            old_changed=True
            WaitForTask(vm.PowerOff())

        vm2 = search.FindByInventoryPath( vsphere_datacenter + '/vm/' + folder_new + '/' + vm_new )
        if vm2 == None:
          vm2 = search.FindByDatastorePath(dc, '[' + vsphere_datastore + '] ' + vm_new + '/' + vm_new + '.vmx')

        if vm2 != None and vm != None:
          move_disks(vm2, vm, si)
 
        if vm2 != None:
          if (hasattr(vm2, 'runtime') and vm2.runtime.powerState == vim.VirtualMachinePowerState.poweredOff) or not hasattr(vm2, 'runtime') :
            new_changed=True
            WaitForTask(vm2.PowerOn())

          wait_for_tools(vm2)
          time.sleep(1)
#         Make sure all Nics connected in case this is a optimized quick vm upgrade swap 
          vmconf = ConnectStateAllNics(vm2, connectstate)
          WaitForTask(vm2.ReconfigVM_Task(vmconf))

# The vm is rebooted first time booted and make sure the vm tools running is not just a glitch
          time.sleep(float(1))
          wait_for_tools(vm2)
          time.sleep(float(poweron_delay))

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        module.fail_json(msg="Caught vmodl fault: %s" % e.msg)
        raise SystemExit(-1)
    except Exception, e:
        print "Caught exception: %s" % str(e)
        module.fail_json("Caught exception: %s" % str(e))
        raise SystemExit(-1)
    rc = None
    out = ''
    err = ''
    result = {}
#    result['poweroff'] = "OK"
    result['vm_new'] = "OK"


#    module.exit_json(**result)
    module.exit_json(changed=(new_changed or old_changed))

# import module snippets
from ansible.module_utils.basic import *

# Start program
if __name__ == "__main__":
    main()

