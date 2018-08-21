#!/usr/bin/env python
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
from ansible.module_utils.basic import *
#from novaclient.v1_1 import client
import yaml
import math
import os
import pytest

def test_availzone(ansible_module):
#    contacted = ansible_module.availzones(atlas_name='Atlas', os_username='admin',traffic_zone='Traffic',ha_zone='HA',os_auth_url='http://137.58.241.5:5000/v2.0/',compute_hosts_in_ddc_zone=1,number_of_ddc_cabinet=2,compute_hosts_in_ha_zone=1,reserved_hosts_json="{''}",ddc_zone='DDC',os_password='admin', force_traffic_zone='True',os_tenant_name='admin', vms_json="[{'hagroup': 'HA', 'vm_type': 'mn', 'vm_numbers': [1], 'vm_basename': 'mn-', 'ip_start_offset': 0, 'vm_end_number': '1'}, {'hagroup': 'HA', 'vm_type': 'mon', 'vm_numbers': [1], 'vm_basename': 'mon-', 'ip_start_offset': 1, 'vm_end_number': '1'}, {'hagroup': 'DDC', 'vm_type': 'ddc', 'vm_numbers': [1], 'vm_basename': 'ddc-', 'ip_start_offset': 2, 'vm_end_number': '2', 'execution_host_index_start': 0}, {'hagroup': 'Traffic1', 'vms_per_host': 1, 'vm_type': 'ts', 'vm_numbers': [1], 'vm_basename': 'ts-', 'ip_start_offset': 4, 'vm_end_number': '0'}, {'hagroup': 'Traffic1', 'vms_per_host': 1, 'vm_type': 'ts', 'vm_numbers': [2], 'vm_basename': 'ts-', 'ip_start_offset': 5, 'vm_end_number': '0'}, {'hagroup': 'Traffic1', 'vms_per_host': 1, 'vm_type': 'slb', 'vm_numbers': [1], 'vm_basename': 'slb-', 'ip_start_offset': 6, 'vm_end_number': '0'}]", dry=True, os_debug_mode=True)

#    contacted2 = ansible_module.availzones(atlas_name='Atlas', os_username='admin',traffic_zone='Traffic',ha_zone='HA',os_auth_url='http://137.58.241.5:5000/v2.0/',compute_hosts_in_ddc_zone=0,number_of_ddc_cabinet=0,compute_hosts_in_ha_zone=1,reserved_hosts_json="{''}",ddc_zone='HA',os_password='admin', force_traffic_zone='False',os_tenant_name='admin', vms_json="[{'hagroup': 'HA', 'vm_type': 'mn', 'vm_numbers': [1], 'vm_basename': 'mn-', 'ip_start_offset': 0, 'vm_end_number': '1'}, {'hagroup': 'HA', 'vm_type': 'mon', 'vm_numbers': [1], 'vm_basename': 'mon-', 'ip_start_offset': 1, 'vm_end_number': '1'}, {'hagroup': 'HA', 'vm_type': 'ddc', 'vm_numbers': [1], 'vm_basename': 'ddc-', 'ip_start_offset': 2, 'vm_end_number': '0', 'execution_host_index_start': 0}, {'hagroup': 'HA', 'vm_type': 'cim', 'vm_numbers': [1], 'vm_basename': 'cim-', 'ip_start_offset': 2, 'vm_end_number': '0'}, {'hagroup': 'Traffic', 'vms_per_host': 2, 'vm_type': 'ts', 'vm_numbers': [1], 'vm_basename': 'ts-', 'ip_start_offset': 4, 'vm_end_number': '1'}, {'hagroup': 'Traffic', 'vms_per_host': 2, 'vm_type': 'ts', 'vm_numbers': [2], 'vm_basename': 'ts-', 'ip_start_offset': 5, 'vm_end_number': '2'}, {'hagroup': 'Traffic', 'vms_per_host': 1, 'vm_type': 'slb', 'vm_numbers': [1], 'vm_basename': 'slb-', 'ip_start_offset': 6, 'vm_end_number': '0'}]", dry=False, os_debug_mode=True)

    contacted2 = ansible_module.availzones(atlas_name='Atlas', os_username='admin',traffic_zone='Traffic',ha_zone='HA',os_auth_url='http://137.58.241.5:5000/v2.0/',compute_hosts_in_ddc_zone=0,number_of_ddc_cabinet=0,compute_hosts_in_ha_zone=1,reserved_hosts_json="{''}",ddc_zone='HA', os_password='admin', force_traffic_zone='False',os_tenant_name='admin', vms_json="[{'hagroup': 'HA', 'vm_type': 'mn', 'vm_numbers': [1], 'vm_basename': 'mn-', 'ip_start_offset': 0, 'vm_end_number': '1'}, {'hagroup': 'HA', 'vm_type': 'mon', 'vm_numbers': [1], 'vm_basename': 'mon-', 'ip_start_offset': 1, 'vm_end_number': '1'}, {'hagroup': 'DDC', 'vm_type': 'ddc', 'vm_numbers': [1], 'vm_basename': 'ddc-', 'ip_start_offset': 2, 'vm_end_number': '2', 'execution_host_index_start': 0}, {'hagroup': 'HA', 'vm_type': 'cim', 'vm_numbers': [1], 'vm_basename': 'cim-', 'ip_start_offset': 2, 'vm_end_number': '0'}, {'hagroup': 'Traffic', 'vms_per_host': 1, 'vm_type': 'ts', 'vm_numbers': [1], 'vm_basename': 'ts-', 'ip_start_offset': 4, 'vm_end_number': '2'}, {'hagroup': 'Traffic', 'vms_per_host': 1, 'vm_type': 'ts', 'vm_numbers': [2], 'vm_basename': 'ts-', 'ip_start_offset': 5, 'vm_end_number': '0'}, {'hagroup': 'Traffic', 'vms_per_host': 1, 'vm_type': 'slb', 'vm_numbers': [1], 'vm_basename': 'slb-', 'ip_start_offset': 6, 'vm_end_number': '2'}, {'hagroup': 'HA', 'vms_per_host': 2, 'vm_type': 'da', 'vm_numbers': [1], 'vm_basename': 'da-', 'ip_start_offset': 7, 'vm_end_number': '2'}]", dry=True, os_debug_mode=True)

#    contacted3 = ansible_module.availzones(atlas_name='Atlas', os_username='admin',traffic_zone='TrafficP',ha_zone='HA',os_auth_url='http://137.58.241.5:5000/v2.0/',compute_hosts_in_ddc_zone=0,number_of_ddc_cabinet=0,compute_hosts_in_ha_zone=1,reserved_hosts_json="{''}",ddc_zone='HA',os_password='admin', force_traffic_zone='True',os_tenant_name='admin', vms_json="[{'hagroup': 'HA', 'vm_type': 'mn', 'vm_numbers': [1], 'vm_basename': 'mn-', 'ip_start_offset': 0, 'vm_end_number': '1'}, {'hagroup': 'HA', 'vm_type': 'mon', 'vm_numbers': [1], 'vm_basename': 'mon-', 'ip_start_offset': 1, 'vm_end_number': '1'}, {'hagroup': 'DDC', 'vm_type': 'ddc', 'vm_numbers': [1], 'vm_basename': 'ddc-', 'ip_start_offset': 2, 'vm_end_number': '2', 'execution_host_index_start': 0}, {'vm_type': 'ts', 'vm_numbers': [1], 'vm_basename': 'ts-', 'ip_start_offset': 4, 'vm_end_number': '1'}, {'hagroup': 'Traffic1', 'vms_per_host': 1, 'vm_type': 'ts', 'vm_numbers': [2], 'vm_basename': 'ts-', 'ip_start_offset': 5, 'vm_end_number': '0'}, {'hagroup': 'Traffic1', 'vms_per_host': 1, 'vm_type': 'slb', 'vm_numbers': [1], 'vm_basename': 'slb-', 'ip_start_offset': 6, 'vm_end_number': '0'}]", dry=True, os_debug_mode=True)


    for (host, result) in  contacted2.items():
        assert 'failed' not in result, result['msg']
        assert 'changed' in result
        assert False, result['debug']

