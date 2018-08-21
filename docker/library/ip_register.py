#!/usr/bin/python
"""
Create the ip<->name Register - Module for Ansible
"""

def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict(
            hostvars=dict(required=True),
        )
    )

    ip_register = register_ips(module.params['hostvars'])

    module.exit_json(ansible_facts={'ip_register': ip_register})

def register_ips(hostvars):
    """Create the register associating ip and hostnames"""

    hosts = [h for h in hostvars['groups']['all']]
    host_list = []

    for host in hosts:
        if host in hostvars:
            host_list.append(hostvars[host])

    ip_register = {}

    for host in host_list:
        if not 'nv_name' in host or not 'ansible_all_ipv4_addresses' in host:
            continue

        nv_name = host['nv_name']
        for ip_addr in host['ansible_all_ipv4_addresses']:
            ip_register[ip_addr] = nv_name

    return ip_register

from ansible.module_utils.basic import *
main()
