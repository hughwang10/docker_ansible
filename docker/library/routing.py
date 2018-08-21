#!/usr/bin/python
"""
Get the Routing Table Module for Ansible
"""

import subprocess
import re

def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict()
    )

    success, data = get_routes()

    if success == False:
        module.fail_json(mgs=data)

    module.exit_json(ansible_facts={'routes': data})

def get_routes():
    """ Get the routes"""

    arguments = ['route', '-n']

    try:
        child = subprocess.Popen(arguments, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout = child.communicate()[0]
        if child.returncode != 0:
            raise subprocess.CalledProcessError(child.returncode, cmd=arguments)
    except subprocess.CalledProcessError:
        return False, stdout

    regex = re.compile(ur'(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*?)\s+(.*)')
    routes = []

    for index, line in enumerate(stdout.splitlines()):
        # Ignore header lines
        if index < 2:
            continue

        match = regex.search(line)

        if match != None:
            route = {
                'destination': match.group(1),
                'gateway': match.group(2),
                'genmask': match.group(3),
                'flags': match.group(4),
                'metric': match.group(5),
                'ref': match.group(6),
                'use': match.group(7),
                'iface': match.group(8),
            }

            routes.append(route)

    return True, routes

from ansible.module_utils.basic import *
main()
