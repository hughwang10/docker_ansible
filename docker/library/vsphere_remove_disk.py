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
module: vsphere_attach_disk
author: MSP Cloud Platform
version_added: "0.0.1"
short_description: Load file to VMWare datastore
requirements: [ pyshpere, pyVmomi ]
description:
    - Load a file to vmware datastore
options:
    disk_scsi_address:
        required: true
        description:
            - disk to delete.

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
import time, string

def FindSCSIDisk(controller, unit, vm):
    return_device = None
    for device in vm.config.hardware.device: 
       if isinstance(device, vim.vm.device.VirtualDisk):
         if (device.unitNumber == unit and (controller+1000) == device.controllerKey): 
           return_device = device
           break         
    return return_device

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
            disk_scsi_addresses=dict(required=True, type='list'),
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
    log = ''
    try:
        si = None
        vsphere_vcenter = module.params.get('vcenter')
        vsphere_vcusername = module.params.get('vcusername').replace("##at##","@")
        vsphere_vcpassword = module.params.get('vcpassword')
        vsphere_datacenter = module.params.get('datacenter')
        vsphere_datastore = module.params.get('datastore')
        vsphere_esxihostname = module.params.get('esxihostname')
        disk_scsi_addresses = module.params.get('disk_scsi_addresses')
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
            print("Could not connect to the specified host using specified "
                  "username and password")
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


        for disk_scsi_address in disk_scsi_addresses:
          disk1 = FindSCSIDisk(0, disk_scsi_address, vm)
          if disk1 != None:
            RemoveDevice(vm, disk1)
            log = log + str(disk_scsi_address) + ","

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
    result['disk_scsi_addresses'] = "OK"
    result['vm_name'] = "OK"


    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

# Start program
if __name__ == "__main__":
    main()

