#!/usr/bin/python
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
"""
Find the Moonshot server based on the iLO webserver signature
Tries to connect to every machine in the network on port 80
Returns the first machine which Server Header contains iLO
"""

from netaddr import IPNetwork
import httplib
from urlparse import urlparse
import socket

def main():
    """ Execution """

    module = AnsibleModule(
        argument_spec=dict(
            subnet=dict(required=True),
            )
        )

    address = find_moonshot(module.params['subnet'])

    if address == None:
        module.fail_json(msg="Moonshot not found")

    module.exit_json(moonshot_address=address)

def gen_subnet(subnet):
    """ Gen addresses in subnet """
    hosts = []
    for host in IPNetwork(subnet):
        hosts.append(host.format())

    return hosts

def find_moonshot(subnet):
    """ Find the Moonshot in the network """
    subnet = gen_subnet(subnet)

    for host in subnet:
        url = urlparse('http://' + host + '/')

        try:
            conn = httplib.HTTPSConnection(host=url.netloc, strict=True, timeout=0.2)
            conn.request('HEAD', url.path)
            resp = conn.getresponse()

            if resp.getheader('Server') != None and 'iLO' in resp.getheader('Server'):
#                return str(resp.getheaders())
                return host

        except socket.error:
            pass

    return None


from ansible.module_utils.basic import *
main()
