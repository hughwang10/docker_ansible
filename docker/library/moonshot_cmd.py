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
Interface Module with the moonshot (based on REST API)
Requires a recent firmware for the moonshot to have the webserver enabled
"""

from base64 import b64encode
import httplib
from urlparse import urlparse
import json

def main():
    """ Execution """

    module = AnsibleModule(
        argument_spec=dict(
            cartridge_exclusion=dict(required=False),
            address=dict(required=True),
            username=dict(required=True),
            password=dict(required=True),
            action=dict(required=False),
            node_uri=dict(required=False),
            state=dict(required=False),
            boot=dict(required=False),
            once=dict(required=False, default=False),
            )
        )

    server = Moonshot(module.params['address'],
                      module.params['username'],
                      module.params['password'])

    if module.params.get('action', None) == 'get_nodes':
        def action():
            nodes = server.get_nodes(module.params['cartridge_exclusion'])
            index = dict()

            for node in nodes:
                index[node['self']] = node

            return index

    if module.params.get('state', None) != None and module.params.get('node_uri', None) != None:
        params = (module.params['node_uri'],
                  module.params['state'])

        action = lambda: server.set_power(*params)

    if module.params.get('boot', None) != None and module.params.get('node_uri', None) != None:
        params = (module.params['node_uri'],
                  module.params['boot'])

        if module.params['once'] == True:
            action = lambda: server.set_bootonce(*params)
        else:
            action = lambda: server.set_boot_order(*params)

    try:
        result = action()
    except ValueError as error:
        module.fail_json(msg=error)

    module.exit_json(cmd_output=result)

class Moonshot(object):
    """ Moonshot representation """

    def __init__(self, address, username, password):
        self.base_url = 'https://' + address
        self.request_headers = dict()

        credentials = b64encode(username + ":" + password)
        self.request_headers['Authorization'] = "BASIC " + credentials

    def do_request(self, operation, uri, body='', headers=None):
        """ Perform a request"""

        url = urlparse(self.base_url + uri)
        conn = httplib.HTTPSConnection(host=url.netloc, strict=True)

        request_headers = self.request_headers

        if headers != None:
            for key, value in headers.iteritems():
                request_headers[key] = value

        conn.request(operation,
                     url.path,
                     headers=request_headers,
                     body=json.dumps(body))

        resp = conn.getresponse()
        body = resp.read()

        try:
            response = json.loads(body.decode('utf-8'))
        except ValueError:
            response = None

        if resp.status == 401:
            raise ValueError('Invalid User credentials')

        # This treat everything but 200 as errors
        if resp.status != 200:
            print response
            raise ValueError('Invalid Request')

        return response

    def get_nodes(self, cartridge_exclusion):
        """ Get Basic info about nodes """
        systems = self.do_request('GET', '/rest/v1/Systems')

        systems = [member['href'] for member in systems['links']['Member']]

        nodes = []

        for system in systems:
            node_raw = self.do_request('GET', system)

            node = dict()

            node['mac'] = node_raw['HostCorrelation']['HostMACAddress']
            node['model'] = node_raw['Model']
            node['name'] = node_raw['Name']
            node['self'] = node_raw['links']['self']['href']

            if not any(x.lower() in node['self'].lower() for x in cartridge_exclusion) and not any(x.lower() in node['model'].lower() for x in cartridge_exclusion):
                nodes.append(node)

        return nodes

    def set_bootonce(self, node_uri, medium):
        """ Setup Bootonce medium """

        body = {"Oem":{"Hp":{"Options":{"BootOnce": medium}}}}
        headers = {'content-type': 'application/json'}

        self.do_request('PATCH', node_uri, body=body, headers=headers)

    def set_boot_order(self, node_uri, media):
        """ Setup Boot order """

        body = {"Oem":{"Hp":{"Options":{"BootOrder": media}}}}
        headers = {'content-type': 'application/json'}

        self.do_request('PATCH', node_uri, body=body, headers=headers)

    def set_power(self, node_uri, value):
        """ Set the power state for the node """

        body = {"Action": "Reset", "ResetType": value}
        headers = {'content-type': 'application/json'}

        self.do_request('POST', node_uri, body=body, headers=headers)



from ansible.module_utils.basic import *
main()
