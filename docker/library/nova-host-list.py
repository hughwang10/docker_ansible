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
from ansible.module_utils.basic import *
#from novaclient.v2 import client
from novaclient.v1_1 import client

module = AnsibleModule(
    argument_spec = dict(
       os_auth_url=dict(required=True, type='str'),
       os_password=dict(required=True, type='str'),
       os_tenant_name=dict(required=True, type='str'),
       os_username=dict(required=True, type='str')
    ),
    supports_check_mode=True
)

servers =[]

try:
    os_auth_url=module.params.get('os_auth_url')
    os_password=module.params.get('os_password')
    os_tenant_name=module.params.get('os_tenant_name')
    os_username=module.params.get('os_username')

    nt = client.Client(os_username, os_password, os_tenant_name, os_auth_url, service_type="compute")
    nhl= nt.hosts.list()
    for ho in nhl:
        if ho.host_name.startswith('compute'):
            if ho.host_name not in servers:
                servers.append(ho.host_name)
except Exception, e:
    print "Caught exception: %s" % str(e)
    raise SystemExit(-1)
                
result = {}
result['servers'] = servers
result['vm_name'] = "OK"

module.exit_json(**result)
