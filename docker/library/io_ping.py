#!/usr/bin/python
"""
IO Ping Module for Ansible
"""

import subprocess

def main():
    """Execution"""
    module = AnsibleModule(
        argument_spec=dict(
            disk=dict(required=True),
            count=dict(required=True),
            size=dict(required=True)
            )
        )

    data = do_io_ping(module.params['disk'], module.params['count'], module.params['size'])

    if data.get('_error', False) == True:
        module.fail_json(msg='Error while performig mtr: ' + data['message'], result=data)

    module.exit_json(changed=False, result=data)


def do_io_ping(disk, count, size):
    """ perform the io ping test """
    args = ["ioping", "-c", count, "-s", size, "-i", "0.2", disk]

    try:
        child = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        stdout = child.communicate()[0]
        if child.returncode != 0:
            raise subprocess.CalledProcessError(child.returncode, cmd=args)
    except subprocess.CalledProcessError as exception:
        return {'_error': True, 'message': stdout, 'disk_name': disk}
    except OSError as exception:
        return {'_error': True, 'message': exception.strerror, 'disk_name': disk}

    disk_regex = re.compile(r"device\s((?:\d|\.)+\s.*)\)")
    disk_size = disk_regex.search(stdout).group(1)

    request_regex = re.compile(r"(\d+)\srequests completed")
    request_completed = request_regex.search(stdout).group(1)

    time_regex = re.compile(r"(\d+\.?\d*\s[m|u]s)\s/\s(\d+\.?\d*\s[m|u]s)\s/\s(\d+\.?\d*\s[m|u]s)\s/\s(\d+\.?\d*\s[m|u]s)")
    time_match = time_regex.search(stdout)

    required_time = {}

    if time_match != None:
        required_time['min'] = convert_time(time_regex.search(stdout).group(1))
        required_time['avg'] = convert_time(time_regex.search(stdout).group(2))
        required_time['max'] = convert_time(time_regex.search(stdout).group(3))
        required_time['mdev'] = convert_time(time_regex.search(stdout).group(4))

    io_result = {
        'disk_name'         : disk,
        'disk_size'         : disk_size,
        'request_completed' : request_completed,
        'required_time'     : required_time,
        'stdout'            : stdout
    }

    return io_result

def convert_time(time_str):
    """ Convertime time string with unit to float in ms"""
    value, unit = time_str.split(' ')
    value = float(value)

    if unit == 'us':
        value /= 1000

    return str(value)

from ansible.module_utils.basic import *
main()

