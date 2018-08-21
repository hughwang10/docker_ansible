#!/usr/bin/python
"""
HTTP Ping Module for Ansible
"""

import subprocess

def main():
    """ Execution"""
    module = AnsibleModule(
        argument_spec=dict(
            destination=dict(required=True),
            count=dict(required=True),
            internalAddress=dict(required=True),
            externalAddress=dict(required=True),
            port=dict(required=True),
            executable=dict(required=True),
        )
    )

    data = do_ping(module.params['count'], module.params['destination'], module.params['internalAddress'], module.params['externalAddress'], module.params['port'], module.params['executable'])

    if data.get('_error', False) == True:
        module.fail_json(msg='Error while performing ping: ' + data['message'], result=data)

    module.exit_json(changed=False, result=data)


def do_ping(count, destination, internal_address, external_address, port, executable):
    """Perform the http ping measure"""

    cmd = [executable, internal_address, external_address, destination, port, count]

    child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = child.communicate()[0]
    if child.returncode != 0:
        return {'_error': True, 'message': output, 'destination': destination + ":" + port}

    failed = 0
    total = count

    failed_regex = re.compile(r"(\d+)\s.+\s(\d+)\s")
    failed_match = failed_regex.search(output)

    if failed_match != None:
        failed = failed_match.group(1)

    rtt_regex = re.compile(r"Avg RTT\s([\d\.]+)\sms")
    rtt_match = rtt_regex.search(output)

    rtt = rtt_match.group(1)

    output = {
        'destination' : destination + ":" + port,
        'rtt'         : rtt,
        'failed'      : failed,
        'total'       : total,
        'stdout'      : output
    }

    return output

from ansible.module_utils.basic import *
main()
