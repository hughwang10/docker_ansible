#!/usr/bin/python
"""
MTR Module for Ansible
"""

import subprocess
import xml.etree.ElementTree as ET
import re

def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict(
            destination=dict(required=True),
            resolve=dict(required=True),
            count=dict(required=True),
            size=dict(required=True),
            interval=dict(required=True),
        )
    )
    data = do_mtr(module.params['destination'], module.params['count'], module.params['resolve'], module.params['size'], module.params['interval'])

    if data.get('_error', False) == True:
        module.fail_json(msg='Error while performig mtr: ' + data['message'], result=data)

    module.exit_json(changed=False, result=data)

def do_mtr(destination, count, resolve, size, interval):
    """
    MTR to the destination
    """
    output = {}
    output['destination'] = destination
    cmd = ['mtr', '--report', '--xml', '-c', count, '-oLSNBAWX', destination]

    if len(size) > 0:
        cmd.extend(['-s', size])

    if len(interval) > 0:
        cmd.extend(['-i', interval])

    if resolve == 'False':
        cmd.append('-n')

    try:
        child = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
        stdout = child.communicate()[0]
        if child.returncode != 0:
            raise subprocess.CalledProcessError(child.returncode, cmd=cmd)
    except subprocess.CalledProcessError as exception:
        return {'_error': True, 'message': stdout, 'destination': destination}
    except OSError as exception:
        return {'_error': True, 'message': exception.strerror, 'destination': destination}

    # The XML for mtr version 0.85 is not valid (it is valid from version 0.86)
    # So we must make it valid
    # Basicaly we just add quotes for the attributes and replace Loss% by Loss

    def repl(match_obj):
        """Replacement function to add the quotes"""
        return '="' + match_obj.group(1) + '"' + match_obj.group(2)

    stdout = re.sub(r'=(.*?)([\s|>])', repl, stdout)
    stdout = re.sub(r'Loss\%', 'Loss', stdout)

    # We extract the data from the XML DOM Tree
    root = ET.fromstring(stdout)
    hubs = []
    for hub in [child for child in root]:
        data = {}
        data['host'] = hub.attrib['HOST']
        for ele in hub:
            data[ele.tag.lower()] = ele.text
        data['loss'] = data['loss'].split('%')[0]
        hubs.append(data)

    output['hubs'] = hubs

    return output

from ansible.module_utils.basic import *
main()
