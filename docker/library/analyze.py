#!/usr/bin/python
"""
Analyse the Results and find problems - Module for Ansible
"""

import uuid

ip_register = {}


def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict(
            hostvars=dict(required=True),
        )
    )

    global ip_register

    ansible_facts = {}

    ip_register = module.params['hostvars']['localhost'].get('ip_register', {})
    global_results = module.params['hostvars']['localhost'].get('global_results', {})

    ansible_facts['server_list'], ansible_facts['problems'] = gather_problems(global_results, module.params['hostvars'])
    ansible_facts['network_problems'] = gather_network_problems(global_results)

    module.exit_json(ansible_facts=ansible_facts)

def size(number):
    """Convert the number to the appropriate unit"""
    current = int(number)

    units = ['P', 'T', 'G', 'M', 'k']
    unit = ''

    while current > 1024:
        current /= 1024
        if len(units) == 0:
            break
        unit = units.pop()

    return str(current) + ' ' + unit



def resolve(ip_addr):
    """Return the Name associated with an ip if possible"""
    return ip_register.get(ip_addr, ip_addr)


def gather_network_problems(global_results):
    """
    Gather the bad links (with loss or delay) and the bad hosts (with an interface with problem)
    """

    link_problems = []
    throughput_problems = []
    host_problems = []

    bad_counter = {}
    total_counter = {}

    for result in [p for p in global_results if p['_test'] == 'ping' and (p['_success'] == False and p.get('_error', False) == False)]:

        bad_counter[result['destination']] = bad_counter.get(result['destination'], 0) + 1

        avg = result.get('rtt', {}).get('avg', '-')
        mdev = result.get('rtt', {}).get('mdev', '-')
        link_problems.append({
            'text': result['interface'] + ': ' + resolve(result['_host']) + ' --> ' + resolve(result['destination']),
            'icon': 'glyphicon glyphicon-transfer',
            'li_attr': {'class': 'text-warning' if int(result['loss']) == 0 else 'text-danger'},
            'children': [
                {'icon': False, 'text':'Loss: ' + result['loss'] + '%'},
                {'icon': False, 'text':'RTT Avg: ' + avg},
                {'icon': False, 'text':'RTT Dev: ' + mdev}
            ]
        })

    for result in [p for p in global_results if p['_test'] == 'iperf' and (p['_success'] == False and p.get('_error', False) == False)]:

        throughput_problems.append({
            'text': resolve(result['_host']) + ' --> ' + resolve(result['destination']),
            'icon': 'glyphicon glyphicon-transfer',
            'li_attr': {'class': 'text-warning'},
            'children': [
                {'icon': False, 'text':'Throughput: ' + size(result['bits_per_second']) + 'bit/s'},
            ]
        })


    for result in [r for r in global_results if r['_test'] == 'ping' and r.get('_error', False) == False]:
        total_counter[result['destination']] = total_counter.get(result['destination'], 0) + 1

    for host, count in bad_counter.iteritems():
        if count > total_counter[host]/2:
            host_problems.append({
                'text': resolve(host) + ': ' + host,
                'icon': 'glyphicon glyphicon-hdd',
            })

    problems = [
        {'text': 'Bad links', 'children': link_problems, 'icon': 'glyphicon glyphicon-th-list'},
        {'text': 'Low throughput', 'children': throughput_problems, 'icon': 'glyphicon glyphicon-th-list'},
        {'text': 'Bad Interface', 'children': host_problems, 'icon': 'glyphicon glyphicon-th-list'}
    ]

    return problems


def gather_problems(global_results, hostvars):
    """Gather all the problems from the test measures"""

    server_list = {}
    server_ko = []
    problems = {}

    for result in global_results:
        if result['_success'] == True:
            continue

        test = result['_test']
        result['_hostname'] = resolve(result['_host'])
        problems.setdefault(test, {}).setdefault(result['_hostname'], [])

        for offender, offenses in result['_offenders'].iteritems():
            for offense in offenses:
                offense['offender'] = offender
                offense['id'] = result['_id']
                problems[test][result['_hostname']].append(offense)

        server_ko.append(result['_host'])

    hosts = [h for h in hostvars['groups']['all']]

    for host in hosts:

        vm_type = hostvars[host].get('nv_type', None)

        if vm_type == None:
            continue

        if not vm_type in server_list:
            server_list[vm_type] = {'ok': [], 'ko': []}

        if host in server_ko:
            server_list[vm_type]['ko'].append(resolve(host))
        else:
            server_list[vm_type]['ok'].append(resolve(host))



    # Formatting server_list for jstree
    server_list_b = []
    for vtype, hosts in server_list.iteritems():
        css_class = 'text-danger' if len(hosts['ko']) > 0 else 'hidden'
        server_list_b.append({
            'text': vtype + ' <span class="burning-bak">&nbsp;<span class="' + css_class + '">' + str(len(hosts['ko'])) + '<i role="presentation" class="glyphicon glyphicon-fire"></i></span></span>',
            'icon': 'glyphicon glyphicon-hdd',
            'li_attr': {'class': 'reference'},
            'children': [
                {
                    'text': 'OK (' + str(len(hosts['ok'])) + ')',
                    'icon': 'glyphicon glyphicon-ok',
                    'li_attr': {'class': 'text-success'},
                    'children': [{'text': h, 'icon': False, 'li_attr': {'class': 'text-success reference'}} for h in  hosts['ok']]
                },
                {
                    'text': 'KO (' + str(len(hosts['ko'])) + ')',
                    'icon': 'glyphicon glyphicon-remove',
                    'li_attr': {'class': 'text-danger'},
                    'state': {'opened': True},
                    'children': [{'text': h, 'icon': False, 'a_attr': {'onclick': 'highlightNode(\'' + h + '\')'}, 'li_attr': {'class': 'text-danger reference'}} for h in  hosts['ko']]
                }
            ]
        })


    # Formatting the problems for jstree
    problems_b = []
    for test, problems in problems.iteritems():
        problems_b.append({
            'text': test,
            'icon': 'glyphicon glyphicon-tasks',
            'children': [
                {
                    'text': hostname,
                    'id': hostname + '_' + str(uuid.uuid4()),
                    'icon': 'glyphicon glyphicon-hdd',
                    'state': {'opened': True},
                    'children': [
                        {
                            'text': v['offender'] + ': ' + v['message'] + '&nbsp;<a onclick="goto(\'' + v['id'] + '\')" href="#' + v['id'] +'"><i class="glyphicon glyphicon-screenshot"></i></a>',
                            'icon': 'glyphicon glyphicon-warning-sign',
                            'children': [
                                {'text': 'Value: ' + str(v['value']), 'icon': False},
                                {'text': 'Expected: ' + v['expected'], 'icon': False} if not isinstance(v['expected'], dict)
                                else
                                {'text': 'Expected', 'icon': False,
                                 'children': [
                                     {
                                         'text': e + ': ' + str(vv),
                                         'icon': False
                                     } for e, vv in v['expected'].iteritems()]
                                }
                            ] + [
                                {'text': name + ': ' + value, 'icon': False}
                                for name, value in (v['extract'].iteritems() if 'extract' in v else {})
                            ]
                        }
                        for v in offenders
                    ]
                }
                for hostname, offenders in problems.iteritems()
            ]
        })


    return server_list_b, problems_b




from ansible.module_utils.basic import *
main()
