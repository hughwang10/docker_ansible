#!/usr/bin/python
"""
Ping Module for Ansible
"""

import subprocess

def main():
    """ Execution"""
    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(required=True),
            count=dict(default="1"),
            timeout=dict(),
            iface=dict(required=True),
            size=dict(),
            interval=dict(),
        )
    )

    data = do_ping(module.params['count'], module.params['timeout'], module.params['dest'], module.params['iface'], module.params['size'], module.params['interval'])

    if data.get('_error', False) == True:
        module.fail_json(msg='Error while performing ping: ' + data['message'], result=data)

    module.exit_json(changed=False, result=data)


def do_ping(count, timeout, destination, interface, size, interval):
    """Perform the ping measure"""

    cmd = ["ping", "-c", count, destination]

    if len(interface) > 0:
        cmd.extend(['-I', interface])

    if len(size) > 0:
        cmd.extend(['-s', size])

    if len(timeout) > 0:
        cmd.extend(['-W', timeout])

    if len(interval) > 0:
        cmd.extend(['-i', interval])

    child = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    output = child.communicate()[0]
    if child.returncode != 0:
        if "ping:" in output:
            return {'_error': True, 'message': output}

    loss_regex = re.compile(r"(\d{1,3})\%")
    loss = loss_regex.search(output).group(1)

    trans_regex = re.compile(r"(\d+)\spackets\strans")
    transmitted = trans_regex.search(output).group(1)

    rtt_regex = re.compile(r"(\d+\.\d+)\/?(\d+\.\d+)\/?(\d+\.\d+)\/?(\d+\.\d+)\/?")
    rtt_match = rtt_regex.search(output)

    rtt = {}

    if rtt_match != None:
        rtt['min'] = rtt_regex.search(output).group(1)
        rtt['avg'] = rtt_regex.search(output).group(2)
        rtt['max'] = rtt_regex.search(output).group(3)
        rtt['mdev'] = rtt_regex.search(output).group(4)

    output = {
        'destination' : destination,
        'interface'   : interface,
        'loss'        : loss,
        'rtt'         : rtt,
        'transmitted' : transmitted,
        'stdout'      : output
    }

    return output

from ansible.module_utils.basic import *
main()
