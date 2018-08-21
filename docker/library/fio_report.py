#!/usr/bin/python
"""
Fio Result Gathering and presenting Module for Ansible
"""

import os
import base64
import fnmatch

def main():
    """ Execution"""
    module = AnsibleModule(
        argument_spec=dict(
            reports=dict(required=True),
            folder=dict(required=True),
            ko=dict(default=False),
        )
    )
    if module.params['ko'] == False:
        data = format_report(module.params['reports'], get_images(module.params['folder']))
    else:
        data = map(lambda x: {'result': {'message': x['stderr'], 'name': x['item']['id'], '_error': True}}, module.params['reports'])

    module.exit_json(changed=True, results=data)

def get_images(folder):
    """Get the smooth graphs and the summery ones"""
    output = {}
    for my_file in os.listdir(folder):
        if fnmatch.fnmatch(my_file, '*smooth.png') or fnmatch.fnmatch(my_file, 'graph*.png'):
            test = my_file.split('-')[0] if len(my_file.split('-')) == 2 else 'graph'
            if not test in output:
                output[test] = {}
            with open(os.path.join(folder, my_file), 'r') as current_file:
                output[test][my_file] = base64.b64encode(current_file.read())

    return output


def format_report(reports, images):
    """Collect and format data for the fio results"""
    results_reports = []

    for report in reports:

        current = {}
        current['success'] = 1

        # Extracting the interesting data from the report
        for operation in ['read', 'write']:
            current[operation] = {
                'bw_global': report['jobs'][0][operation]['bw'],
                'bw_min': report['jobs'][0][operation]['bw_min'],
                'bw_max': report['jobs'][0][operation]['bw_max'],
                'bw_avg': report['jobs'][0][operation]['bw_mean'],
                'clat_min': report['jobs'][0][operation]['clat']['min'],
                'clat_max': report['jobs'][0][operation]['clat']['max'],
                'clat_avg': report['jobs'][0][operation]['clat']['mean'],
                'iops': report['jobs'][0][operation]['iops']
            }

        current['name'] = report['jobs'][0]['jobname']
        current['images'] = images[current['name']] if current['name'] in images else {}
        results_reports.append(current)

    # Compute the average for all the measures

    tmp = {}
    for operation in ['read', 'write']:
        tmp[operation] = {}
        measures = ['bw_global', 'bw_min', 'bw_max', 'bw_avg', 'clat_min', 'clat_max', 'clat_avg', 'iops']
        for measure in measures:
            tmp[operation][measure] = sum([t[operation][measure] for t in results_reports if int(t[operation][measure]) != 0]) * 1.0 / len([t[operation][measure] for t in results_reports if t[operation]['iops'] != 0.0]) if len([t[operation][measure] for t in results_reports if t[operation]['iops'] != 0.0]) != 0 else 0

    tmp['name'] = 'global'
    tmp['images'] = images['graph'] if 'graph' in images else {}
    results_reports.append(tmp)

    # To be compatible with the output of the other modules
    return map(lambda x: {'result': x}, results_reports)


from ansible.module_utils.basic import *
main()
