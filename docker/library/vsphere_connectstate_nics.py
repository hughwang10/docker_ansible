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
module: vsphere_connectstate_nics
author: MSP Cloud Platform
version_added: "0.0.1"
short_description: Load file to VMWare datastore
requirements: [ pyshpere, pyVmomi ]
description:
    - Remap adaptors and networks (portgroups)
options:
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

    vm_name:
        required: true
        description:
            - Guest name

    nics_connected:
        required: true
        description:
            - True or False

'''

import atexit
import time

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect
from pyVim.task import WaitForTask

import time, string

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

def get_obj(content, vimtype, name):
    """
    Get the vsphere object associated with name
    """
    obj = None
    container = content.viewManager.CreateContainerView(content.rootFolder, vimtype, True)
    for c in container.view:
        if c.name == name:
            obj = c
            break
    return obj

def main():
    module = AnsibleModule(
        argument_spec = dict(
            vm_name=dict(required=True, type='str'),
            nics_connected=dict(required=True, type='bool'),
            vcenter=dict(required=True, type='str'),
            vcusername=dict(required=True, type='str'),
            vcpassword=dict(required=True, type='str'),
            datacenter=dict(required=True, type='str'),
            datastore=dict(required=True, type='str'),
            esxihostname=dict(required=True, type='str'),
        ),
        supports_check_mode=True
    )
    log = 'xx'
    try:
        si = None
        vsphere_vcenter = module.params.get('vcenter')
        vsphere_vcusername = module.params.get('vcusername').replace("##at##","@")
        vsphere_vcpassword = module.params.get('vcpassword')
        vsphere_datacenter = module.params.get('datacenter')
        vsphere_datastore = module.params.get('datastore')
        vsphere_esxihostname = module.params.get('esxihostname')
        vm_name = module.params.get('vm_name')
        connectstate = module.params.get('nics_connected')
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

        datacenters = [entity for entity in content.rootFolder.childEntity
                        if hasattr(entity, 'vmFolder')]
        dc = None
        for datacenter in datacenters:
            if datacenter.name == vsphere_datacenter:
                dc = datacenter

        search = content.searchIndex
        vm = search.FindByDatastorePath(dc, '[' + vsphere_datastore + '] ' + vm_name + '/' + vm_name + '.vmx')
        vmconf = ConnectStateAllNics(vm, connectstate)
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
    result['nic_ids'] = "OK"
    result['network_names'] = "OK"

    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

# Start program
if __name__ == "__main__":
    main()

