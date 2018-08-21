#!/usr/bin/python
"""
Test Playbook Generation Module for Ansible
"""

from copy import deepcopy
from math import ceil

def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict(
            default_parameters=dict(default=None),
            tests=dict(required=True),
            networks=dict(required=True),
            vm_specs=dict(required=True),
            hostvars=dict(required=True),
        )
    )

    try:
        data = gen_playbook(module.params['default_parameters'], module.params['tests'], module.params['networks'], module.params['vm_specs'], module.params['hostvars'])
    except ValueError as exception:
        module.fail_json(msg=str(exception))


    runtime = estimate_runtime(data, module.params['hostvars'])
    runtime = int(ceil(runtime / 60))

    module.exit_json(tasks=data, runtime=runtime)


def gen_playbook(default_parameters, tests, networks, vm_specs, hostvars):
    """ Generate an ansible playbook"""

    # Build the name <-> table
    dns = dict((v['nv_name'], k) for k, v in hostvars.iteritems() if 'nv_name' in v)

    tasks = []
    for test in tests:
        tasks.extend(gen_task(test, networks, default_parameters, vm_specs, dns))

    # We group all the tasks for one host
    roles_by_host = {}
    for task in tasks:
        roles_by_host.setdefault(task['hosts'], []).extend(task['roles'])

    tasks = []
    for host, roles in roles_by_host.iteritems():
        tasks.append({
            'hosts': host,
            'gather_facts': False,
            'roles': roles
        })


    return tasks

def gen_task(test, networks, default_parameters, vm_specs, dns):
    """Generate a task"""

    tasks = []

    hosts = test['hosts']
    if not isinstance(hosts, list):
        if hosts == 'all':
            hosts = [t for t in vm_specs]
        else:
            hosts = [hosts]

    for host in hosts:

        try:
            resolved_host = dns.get(host, host)
        except TypeError:
            resolved_host = host

        task = {
            'hosts': resolved_host,
            'gather_facts': 'no'
        }

        roles = []
        sub_tests = []

        if 'networks' in test:
            nets = test['networks'] if isinstance(test['networks'], list) else [test['networks']]
            if nets == ['all']:
                if host not in [t for t in vm_specs]:
                    raise ValueError('You cannot use networks=all with hosts described by an IP')
                nets = vm_specs[host]['networks']

            for net in nets:
                sub_test = deepcopy(test)
                if not net in vm_specs[host]['networks']:
                    continue

                if not 'parameters' in sub_test:
                    sub_test['parameters'] = {}

                sub_test['parameters']['destinations'] = networks[net]['hosts']
                sub_test['parameters']['gateway'] = networks[net]['gateway']
                sub_test['parameters']['interface'] = networks[net]['iface']
                sub_test['parameters']['label'] = networks[net]['name']
                sub_tests.append(sub_test)
        else:
            sub_tests = [test]

        for meas in sub_tests:

            params = default_parameters.get(meas['test'], {})

            for param, value in meas.get('parameters', {}).iteritems():
                params[param] = value

            if not isinstance(params.get('destinations', []), list):
                params['destinations'] = [params['destinations']]

            if not isinstance(params.get('disks', []), list):
                params['disks'] = [params['disks']]

            # Replace node names in destinations
            if 'destinations' in params:
                new_dests = []
                for dest in params['destinations']:
                    try:
                        new_dests.append(dns.get(dest, dest))
                    except TypeError:
                        new_dests.append(dest)
                params['destinations'] = new_dests

            role = {}

            if meas['test'] == 'ping':

                role = {
                    'role': 'ping',
                    'interface': params.get('interface', None),
                    'count': params.get('count', None),
                    'timeout': params.get('timeout', None),
                    'size': params.get('size', None),
                    'interval': params.get('interval', None),
                    'tags': ['ping'],
                    'destinations': params['destinations'] + [params.get('gateway', None)],
                }

            if meas['test'] == 'http_ping':

                role = {
                    'role': 'http_ping',
                    'interface': params.get('interface', None),
                    'externalAddress': params.get('externalAddress', None),
                    'port': params.get('port', None),
                    'count': params.get('count', None),
                    'tags': ['http_ping'],
                    'destinations': params['destinations'],
                }

            if meas['test'] == 'host_info':

                role = {
                    'role': 'host_info',
                    'tags': ['host_info'],
                    'host_info': params['host_info']
                }

            if meas['test'] == 'mtr':

                role = {
                    'role': 'mtr',
                    'tags': ['mtr'],
                    'destinations': params['destinations'],
                    'resolve': params.get('resolve', None),
                    'size': params.get('size', None),
                    'count': params.get('count', None),
                    'interval': params.get('interval', None),
                }

            if meas['test'] == 'iperf':

                role = {
                    'role': 'iperf',
                    'tags': ['iperf'],
                    'duration': params.get('duration', None),
                    'port': params.get('port', None),
                    'destinations': params['destinations'],
                    'no_server': params.get('no_server', None)
                }

            if meas['test'] == 'io_ping':

                role = {
                    'role': 'io_ping',
                    'tags': ['io_ping'],
                    'disks': params['disks'],
                    'count': params.get('count', None),
                    'size': params.get('size', None)
                }

            if meas['test'] == 'fio':

                role = {
                    'role': 'fio',
                    'configs': params['configs'],
                    'tags': ['fio'],
                    'dummy': params.get('dummy', False),
                    'debug': params.get('debug', False),
                    'fio_output_dir': params.get('fio_output_dir', None)
                }



            to_delete = []
            for key, value in role.iteritems():
                if value == None:
                    to_delete.append(key)

            for key in to_delete:
                role.pop(key)

            roles.append(role)

            if role['role'] in ['ping', 'mtr', 'iperf', 'io_ping', 'fio', 'host_info', 'http_ping']:
                roles.append({
                    'role': 'record',
                    'test_name': role['role'],
                    'tags': role['tags'],
                    'label': params.get('label', 'default'),
                })


        task['roles'] = roles
        tasks.append(task)


    return tasks

def estimate_runtime(tasks, hostvars):
    """ Estimate the runtime of the playbook (in seconds) """

    forks = int(hostvars.get('forks', 5))

    total_time = 0

    # Estimated time for data parsing
    total_time += 5

    # Estimating Gathering facts time
    total_time += 80 * ((len(hostvars['groups']['all']) - 1) / forks + 1)

    for task in tasks:

        nb_hosts = len(hostvars['groups'].get(task['hosts'], []))
        nb_batch = (nb_hosts - 1) / forks + 1

        batch_time = 20

        for role in task['roles']:
            batch_time += estimate_runtime_role(role)

        total_time += batch_time * nb_batch

    return total_time

def estimate_runtime_role(role):
    """ Estimate the runtime of a role """

    role_time = 0

    if role['role'] in ['mtr', 'ping']:
        role_time = len(role['destinations']) * (role.get('count', 5) * role.get('interval', 0.2) + 0.5)
    elif role['role'] == 'iperf':
        role_time = 2 + len(role['destinations']) * role.get('duration', 5)
    elif role['role'] == 'io_ping':
        role_time = len(role['disks']) * (role.get('count', 5) * 0.2 + 0.5)
    elif role['role'] == 'host_info':
        role_time = 2
    elif role['role'] == 'fio':
        role_time = 0
        for config in role['configs']:
            role_time += config['runtime']

    return role_time

from ansible.module_utils.basic import *
main()
