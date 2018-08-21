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
module: vsphere_update_vm
author: MSP Cloud Platform
version_added: "0.0.1"
short_description: Update vm config
requirements: [ pyshpere, pyVmomi ]
description:
    - Load a file to vmware datastore
options:
    time_sync:
        required: true
        description:
            - time sync flag, vm sync to host.

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

def SetPowerOffMode(vm1, poweroff):
   cspec = vim.vm.ConfigSpec()
   tools = vim.vm.ToolsConfigInfo()
   tools.beforeGuestShutdown = False
   tools.toolsUpgradePolicy = 'upgradeAtPowerCycle'
   cspec.tools = tools
   powerOp = vim.vm.DefaultPowerOpInfo()
   powerOp.defaultPowerOffType = poweroff 
   powerOp.powerOffType = poweroff
   cspec.powerOpInfo = powerOp
   WaitForTask(vm1.Reconfigure(cspec))


def SetTimeSync(vm1, timesync = True):
   # Helper to do the removal of a single device.
   cspec = vim.vm.ConfigSpec()
   tools = vim.vm.ToolsConfigInfo()
   tools.syncTimeWithHost = timesync
   cspec.tools = tools
   WaitForTask(vm1.Reconfigure(cspec))
   return vm1

def main():
    module = AnsibleModule(
        argument_spec = dict(
            time_sync=dict(required=True, type='bool'),
            poweroff_mode=dict(required=False, choices=['hard', 'soft'], type='str'),
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
        time_sync = module.params.get('time_sync')
        poweroff_mode = module.params.get('poweroff_mode')
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

        SetTimeSync(vm, time_sync)
 
        if len(poweroff_mode) > 0:
          SetPowerOffMode(vm, poweroff_mode) 


    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        raise SystemExit(-1)
    except Exception, e:
        e = sys.exc_info()[0]
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

