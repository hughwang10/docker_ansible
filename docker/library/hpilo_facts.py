#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2012 Dag Wieers <dag@wieers.com>
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

DOCUMENTATION = '''
---
author: Dag Wieers
module: hpilo_facts
short_description: Gather facts through an HP iLO interface
description:
  - This module gathers facts for a specific system using its HP iLO interface.
    These facts include hardware and network related information useful
    for provisioning (e.g. macaddress, uuid).
  - This module requires the hpilo python module.
version_added: "0.8"
options:
  host:
    description:
      - The HP iLO hostname/address that is linked to the physical system.
    required: true
  login:
    description:
      - The login name to authenticate to the HP iLO interface.
    default: Administrator
  password:
    description:
      - The password to authenticate to the HP iLO interface.
    default: admin
examples:
  - description: Task to gather facts from a HP iLO interface only if the system is an HP server
    code: |
      - local_action: hpilo_facts host=$ilo_address login=$ilo_login password=$ilo_password
        only_if: "'$cmdb_hwmodel'.startswith('HP ')
      - local_action: fail msg="CMDB serial ($cmdb_serialno) does not match hardware serial ($hw_system_serial) !"
        only_if: "'$cmdb_serialno' != '$hw_system_serial'"
  - description: Typical output of HP iLO_facts for a physical system
    code: |
      - hw_bios_date: "05/05/2011"
        hw_bios_version: "P68"
        hw_eth0:
        - macaddress: "00:11:22:33:44:55"
          macaddress_dash: "00-11-22-33-44-55"
        hw_eth1:
        - macaddress: "00:11:22:33:44:57"
          macaddress_dash: "00-11-22-33-44-57"
        hw_eth2:
        - macaddress: "00:11:22:33:44:5A"
          macaddress_dash: "00-11-22-33-44-5A"
        hw_eth3:
        - macaddress: "00:11:22:33:44:5C"
          macaddress_dash: "00-11-22-33-44-5C"
        hw_eth_ilo:
        - macaddress: "00:11:22:33:44:BA"
          macaddress_dash: "00-11-22-33-44-BA"
        hw_product_name: "ProLiant DL360 G7"
        hw_product_uuid: "ef50bac8-2845-40ff-81d9-675315501dac"
        hw_system_serial: "ABC12345D6"
        hw_uuid: "123456ABC78901D2"
notes:
  - This module ought to be run from a system that can access the HP iLO
    interface directly, either by using local_action or
    using delegate_to.
'''

import sys
import warnings
try:
    import hpilo
except ImportError:
    print "failed=True msg='hpilo python module unavailable'"
    sys.exit(1)

# Surpress warnings from hpilo
warnings.simplefilter('ignore')

def main():

    module = AnsibleModule(
        argument_spec = dict(
            host = dict(required=True),
            login = dict(default='Administrator'),
            password = dict(default='admin'),
        )
    )

    host = module.params.get('host')
    login = module.params.get('login')
    password = module.params.get('password')

    ilo = hpilo.Ilo(host, login=login, password=password)

    # TODO: Count number of CPUs, DIMMs and total memory
    data = ilo.get_host_data()
    facts = {
        'module_hw': True,
    }
    for entry in data:
        if not entry.has_key('type'): continue
        if entry['type'] == 0: # BIOS Information
            facts['hw_bios_version'] = entry['Family']
            facts['hw_bios_date'] = entry['Date']
        elif entry['type'] == 1: # System Information
            facts['hw_uuid'] = entry['UUID']
            facts['hw_system_serial'] = entry['Serial Number'].rstrip()
            facts['hw_product_name'] = entry['Product Name']
            facts['hw_product_uuid'] = entry['cUUID']
        elif entry['type'] == 209: # Embedded NIC MAC Assignment
            for (name, value) in [ (e['name'], e['value']) for e in entry['fields'] ]:
                if name.startswith('Port'):
                    try:
                        factname = 'hw_eth' + str(int(value) - 1)
                    except:
                        factname = 'hw_eth_ilo'
                elif name.startswith('MAC'):
                    facts[factname] = {
                        'macaddress': value.replace('-', ':'),
                        'macaddress_dash': value
                    }
        elif entry['type'] == 209: # HPQ NIC iSCSI MAC Info
            for (name, value) in [ (e['name'], e['value']) for e in entry['fields'] ]:
                if name.startswith('Port'):
                    try:
                        factname = 'hw_iscsi' + str(int(value) - 1)
                    except:
                        factname = 'hw_iscsi_ilo'
                elif name.startswith('MAC'):
                    facts[factname] = {
                        'macaddress': value.replace('-', ':'),
                        'macaddress_dash': value
                    }

    module.exit_json(ansible_facts=facts)

# this is magic, see lib/ansible/module_common.py
#<<INCLUDE_ANSIBLE_MODULE_COMMON>>
main()

