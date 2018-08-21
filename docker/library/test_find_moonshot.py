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

def test_find_moonshot(ansible_module):
#    contacted = ansible_module.find_moonshot(subnet='137.58.220.0/22')
    contacted = ansible_module.find_moonshot(subnet='137.58.222.0/24')



    for (host, result) in contacted.items():
        assert 'failed' not in result, result['msg']
        assert 'changed' in result
#        print result['moonshot_address']
        assert False, 'iLO address is: ' + result['moonshot_address']

