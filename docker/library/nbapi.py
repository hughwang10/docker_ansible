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
MSA Northbound API  Module for Ansible
"""

import atexit
import subprocess
import json
import time
import os
from StringIO import StringIO

def read_nbapi(url, user, password, datafile):
    """
    read object(s) from MSA Northbound API
    """
    returncode = True
    arguments = ['curl', '-k', '-u', user + ':' + password, '-H', '"Content-type: application/json"', url, '-o', datafile, '--retry-max-time', '60' ]

    try:
#       child = subprocess.Popen(arguments, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
       returncode = subprocess.call(arguments, stdin=None, stdout=None, stderr=None, shell=False)
    except subprocess.CalledProcessError:
       return {'_error': True, 'message': 'Tried: curl' + url}

    return { '_error' : returncode, 'message': 'OK' }

def write_nbapi(url, user, password, datafile):
    """
    write object(s) to MSA Northbound API
    """
    returncode = True
    arguments = ['curl', '-k', '-X', 'PUT', '-u', user + ':' + password, '-H', '"Content-type: application/json"', url, '--data-binary', '"@' + datafile +'"', '--retry-max-time', '60' ]

    try:
#        child = subprocess.Popen(arguments, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        returncode = subprocess.call(arguments, stdin=None, stdout=None, stderr=None, shell=False)
    except subprocess.CalledProcessError:
       return {'_error': True, 'message': 'Tried: curl' + url }

    return { '_error' : returncode, 'message': 'OK' }

def main():
    """
     Execution
    """
    data = { '_error': False, 'message': '' }
    module = AnsibleModule(
        argument_spec=dict(
            user=dict(required=True, type='str'),
            password=dict(required=True, type='str'),
            host=dict(required=True, type='str'),
            operation=dict(required=False, choices=['GET', 'PUT'], type='str'),
            command=dict(required=True, type='str'),
            command_basepath=dict(default=":9443/msa/api/", type='str'),
            data_file=dict(required=True, type='str')
        )
    )
    try:
        nbapi_user = module.params.get('user')
        nbapi_password = module.params.get('password')
        nbapi_host = module.params.get('host')
        nbapi_operation = module.params.get('operation')
        nbapi_command = module.params.get('command')
        nbapi_command_basepath = module.params.get('command_basepath')
        nbapi_data_file = module.params.get('data_file')
        url_nbapi='https://' + nbapi_host + nbapi_command_basepath + nbapi_command

        if nbapi_operation == 'GET':
            data = read_nbapi(url_nbapi, nbapi_user, nbapi_password, nbapi_data_file)

        else:
            data = write_nbapi(url_nbapi, nbapi_user, nbapi_password, nbapi_data_file)

        if data.get('_error', False) == True:
            module.fail_json(msg=data['message'], result=data)

    except Exception, e:
        print "Caught exception: %s" % str(e)
        raise SystemExit(-1)
    module.exit_json(changed=True, result=None)
# import module snippets
from ansible.module_utils.basic import *

# Start program
if __name__ == "__main__":
    main()

