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
Iperf Module for Ansible
"""

import subprocess
import json
import time
import os
from StringIO import StringIO

def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict(
            port=dict(default=None),
            destination=dict(required=True),
            duration=dict(default=5),
            action=dict(required=True),
        )
    )

    if module.params['action'] == 'start':
        data = start_iperf(module.params['destination'], port=module.params['port'])

    else:
        data = iperf(module.params['destination'], module.params['duration'], port=module.params['port'])

    if data.get('_error', False) == True:
        module.fail_json(msg=data['message'], result=data)

    module.exit_json(changed=True, result=data)

def start_iperf(destination, port=None):
    """
    Find a free port for the iperf daemon
    """
    output = {}
    output['destination'] = destination
    aport=port

    if port == None:
        aport = 6665

    free = False

    while free == False:
        try:
            # This suppose the script has been copied before to the target host
            arguments = ['nohup', 'iperf3', '-s', '-p',  str(aport)]

            child = subprocess.Popen(arguments, preexec_fn=os.setpgrp, stderr=subprocess.STDOUT, stdout=open('/dev/null', 'w'))
            time.sleep(0.1)
            if child.poll() != None:
                raise subprocess.CalledProcessError(child.returncode, cmd=arguments)
            free = True
            output['pid'] = child.pid
        except subprocess.CalledProcessError:
            aport += 1
            # If we have too many fails we give up
            if aport > 6700:
                return {'_error': True, 'message': 'Too many failed attempts to launch iperf3', 'destination': destination}

    output['port'] = aport

    return output

def iperf(destination, duration, port=None):
    """
    Perform Iperf measurement to the destination
    """
    output = {}
    output['destination'] = destination
    arguments = ['iperf3', '-J', '-t', duration, '-c', destination]

    if port != None:
        arguments.extend(['-p', str(port)])

    try:
        child = subprocess.Popen(arguments, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout = child.communicate()[0]
        if child.returncode != 0:
            raise subprocess.CalledProcessError(child.returncode, cmd=arguments)
    except subprocess.CalledProcessError as exception:
        output['_error'] = True
        output['message'] = stdout
        return output
    except OSError as exception:
        output['_error'] = True
        output['message'] = exception.strerror
        return output

    if "failed" in stdout:
        output['_error'] = True
        output['message'] = stdout
        return output

    # We get the data from the CSV output of iperf
    json_file = StringIO(stdout)
    reader = json.load(json_file)
    output['bits_per_second'] = str(int(reader['end']['sum_received']['bits_per_second']))
    output['bytes'] = str(int(reader['end']['sum_received']['bytes']))
    output['start'] = str(int(reader['end']['sum_received']['start']))
    output['end'] = str(int(reader['end']['sum_received']['end']))

    return output

from ansible.module_utils.basic import *
main()
