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
'''
Copyright 2014-2015 Reubenur Rahman
All Rights Reserved
@author: reuben.13@gmail.com
'''
DOCUMENTATION = '''
---
module: vsphere_list_hosts
author: MSP Cloud Platform
version_added: "0.0.1"
short_description: Update vm config
requirements: [ pyshpere, pyVmomi ]
description:
    - Load list of hosts and respective resource pool
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

'''

import atexit
import time

from pyVmomi import vim, vmodl
from pyVim import connect
from pyVim.connect import Disconnect

import time

def main():
    module = AnsibleModule(
        argument_spec = dict(
            vcenter=dict(required=True, type='str'),
            vcusername=dict(required=True, type='str'),
            vcpassword=dict(required=True, type='str'),
            datacenter=dict(required=True, type='str')
#            datastore=dict(required=True, type='str'),
#            esxihostname=dict(required=True, type='str')
        ),
        supports_check_mode=True
    )
    resultstring = []
    hosts_results = []
    clusters_results = {}
    try:
        si = None
        vsphere_vcenter = module.params.get('vcenter')
        vsphere_vcusername = module.params.get('vcusername').replace("##at##","@")
        vsphere_vcpassword = module.params.get('vcpassword')
        vsphere_datacenter = module.params.get('datacenter')
#        vsphere_datastore = module.params.get('datastore')
#        vsphere_esxihostname = module.params.get('esxihostname')
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

         # Search for all ESXi hosts
        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.HostSystem],
                                                          True)
        esxi_hosts = objview.view
        objview.Destroy()

        objview = content.viewManager.CreateContainerView(content.rootFolder,
                                                          [vim.ComputeResource],
                                                          True)

        clusters = objview.view
        host_list = {}

        for esxi_host in esxi_hosts:
            host_list[esxi_host.name] = {}
            host_list[esxi_host.name] = esxi_host.name
        for index, cluster in enumerate(clusters):
            clusters_results['hosts'] = {}
            for host in cluster.host:
               host_list[host.name] = {}
               host_list[host.name]['resource_name'] = cluster.name
            clusters_results = host_list

    except vmodl.MethodFault, e:
        print "Caught vmodl fault: %s" % e.msg
        raise SystemExit(-1)
    except Exception, e:
        print "Caught exception: %s" % str(e)
        raise SystemExit(-1)
    result = {}
    result['hosts'] = clusters_results
    result['vm_name'] = "OK"


    module.exit_json(**result)

# import module snippets
from ansible.module_utils.basic import *

# Start program
if __name__ == "__main__":
    main()

