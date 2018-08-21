#!/usr/bin/python
"""
Perform Success check on all the results - Module for Ansible
"""

import math
import cPickle
from copy import deepcopy

def main():
    """
     Execution
    """
    module = AnsibleModule(
        argument_spec=dict(
            hostvars=dict(required=True),
            rules=dict(required=True),
        )
    )

    results = get_results(module.params['hostvars'])
    export_results = deepcopy(results)

    autotune_rules = {}
    rules = module.params['rules']
    check_all(rules, results, autotune_rules)

    module.exit_json(ansible_facts={'global_results': results, 'local_results': {}, 'autotune_rules': autotune_rules, 'export_results': export_results})


def get_results(hostvars):
    """ Get the results """

    results = []

    # If data was imported
    if len(hostvars['localhost'].get('import_results', [])) > 0:
        return hostvars['localhost'].get('import_results', [])

    for host in [data for host, data in hostvars.iteritems() if host in hostvars['groups']['all']]:
        results.extend(host.get('results', []))

    return results


def check_all(rules, results, autotune_rules):
    """Perform all the checks for the test and invariant rules"""


    # Find all the groups and labels
    group_list = []
    label_list = []
    for result in results:
        group_list.append(result['_group'])
        label_list.append(result['_label'])

        if result.get('_error', False) == True:
            result['_success'] = False
            result.setdefault('_offenders', {}).setdefault('Error', []).append({
                'message': result.get('message', ''),
                'value': '',
                'expected': '',
                'extract': {}
            })

    group_list = set(group_list)
    label_list = set(label_list)

    for group, tests in rules.iteritems():
        context = {'test_group': group}
        for test, test_checks in tests.iteritems():
            context['test'] = test
            local_results = [r for r in results if r['_test'] == test and (r['_group'] == group or group == 'global')]
            if len(results) == 0:
                continue
            for check in test_checks:
                context.pop('group', None)
                context.pop('label', None)
                if check.get('scope', None) == 'group':
                    for current_group in group_list:
                        rss = [r for r in local_results if r['_group'] == current_group]
                        context['group'] = current_group
                        check_invariant(rss, check, autotune_rules, context)
                elif check.get('scope', None) == 'group_and_label':
                    for current_group in group_list:
                        context['group'] = current_group
                        for current_label in label_list:
                            rss = [r for r in local_results if r['_group'] == current_group and r['_label'] == current_label]
                            context['label'] = current_label
                            check_invariant(rss, check, autotune_rules, context)
                elif check.get('scope', None) == 'label':
                    for current_label in label_list:
                        context['label'] = current_label
                        rss = [r for r in local_results if r['_label'] == current_label]
                        check_invariant(rss, check, autotune_rules, context)
                else:
                    check_invariant(local_results, check, autotune_rules, context)


def get_argument(obj, argument, wildcard=False):
    """Get the value needed for the test"""
    objs = [obj]
    for part in argument.split('.'):
        try:
            if part == '*':
                new_objs = []
                for ele in objs:
                    new_objs.extend(ele)
                objs = new_objs
            else:
                objs = map(lambda x: x[part], objs)
        except KeyError:
            return [None] if wildcard else None
        except TypeError:
            return [None] if wildcard else None

    return objs if wildcard else objs[0]

def check_invariant(elements, rule, autotune_rules, context):
    """Check that elements respect the invariant"""
    if 'when' in rule:
        elements = [e for e in elements if complies(e, rule['when'])]

    # First we build the function to get the left Operand
    if rule['attribute'] == 'value':
        func = lambda x: get_argument(x, rule['argument'], wildcard=True)
    elif rule['attribute'] == 'len':
        func = lambda x: map(len, get_argument(x, rule['argument'], wildcard=True)) if get_argument(x, rule['argument']) != None else None
    elif rule['attribute'] == 'pickle':
        func = lambda x: map(cPickle.dumps, get_argument(x, rule['argument'], wildcard=True)) if get_argument(x, rule['argument']) != None else None
    else:
        raise ValueError(rule['attribute'])

    # If we have a invariant kind of rule we have to compute the Right operand
    if rule.get('invariant', None) == True:

        # We flatten the element to check
        eles = []
        for ele in [e for e in map(func, elements) if e != None]:
            if isinstance(ele, list):
                eles.extend([i for i in ele if i != None])
            else:
                eles.append(ele)

        if len(eles) == 0:
            return

        most, _ = most_common(eles)
        reference = most

        if rule['type'] == 'distance':
            eles = [float(e) for e in eles if e != None]
            madi = mad(eles)
            mediani = median(eles)

            reference = {
                'mad': madi,
                'median': mediani,
                'coef': rule.get('coef', 1),
                'offset': float(rule.get('offset', 0))
            }

            # Variables for the STDEV Range Test
            #avg = average(eles)
            #stdev = stddev(eles)
            #mini = min(eles)
            #maxi = max(eles)
    else:
        reference = rule['value']

    if rule.get('autotune', None) == True:
        autotune_check = {
            'argument': rule['argument'],
            'attribute': rule['attribute'],
            'type': rule['type'],
            'scope': rule.get('scope', None),
            'coef': rule.get('coef', None),
            'message': rule.get('message', None),
            'extract': rule.get('extract', None),
            'when': rule.get('when', {}),
            'value': reference,
            'source': 'autotuning',
        }

        if 'label' in context:
            autotune_check['when']['_label'] = context.get('label', None)


        # Remove key with None Value
        autotune_check = dict((k, v) for k, v in autotune_check.iteritems() if v != None)
        rule_group = context.get('group', context['test_group'])
        autotune_rules.setdefault(rule_group, {}).setdefault(context['test'], []).append(autotune_check)


    # We define the comparison functions that have to work on lists

    def is_compared(aaa, bbb, comparator):
        """Equality comparator"""
        if isinstance(aaa, list):
            for ele in [i for i in aaa if i != None]:
                if not is_compared(ele, bbb, comparator)[0]:
                    return (False, ele, bbb)
            return (True, '', '')
        else:
            return (True, '', '') if comparator(aaa, bbb) else (False, aaa, bbb)

    for ele in elements:

        raw_value = func(ele)
        if raw_value == None:
            continue

        test = True

        if rule['type'] == 'exact':
            if rule.get('numerical', None) == True:
                comparator = lambda x, y: float(x) == float(y)
            else:
                comparator = is_equal
            test, value, expected = is_compared(raw_value, reference, comparator)
        elif rule['type'] == 'greater':
            test, value, expected = is_compared(raw_value, reference, lambda x, y: float(x) > float(y))
        elif rule['type'] == 'lesser':
            test, value, expected = is_compared(raw_value, reference, lambda x, y: float(x) < float(y))
        elif rule['type'] == 'distance':
            test, value, expected = is_compared(raw_value, reference, lambda x, y: abs(float(x) - y['median']) <= y['coef'] * y['mad'] + y['offset'])

        expected = expected if rule['attribute'] != 'pickle' else 'Serialization'
        if isinstance(expected, dict):
            expected = dict(expected)
            expected.update({'Attribute': rule['attribute'], 'Type': rule['type']})
        else:
            expected = str(expected) + ' (' + rule['attribute'] +' | ' + rule['type'] + ')'

        value = 'Serialization' if rule['attribute'] == 'pickle' else str(value)


        if not test:
            ele['_success'] = False
            ele.setdefault('_offenders', {}).setdefault(rule['argument'], []).append({
                'message': rule['message'] if 'message' in rule else '',
                'value': value,
                'expected': expected,
                'extract': get_extracted(ele, rule['extract']) if 'extract' in rule else {}
            })

def is_number(value):
    """ Check is a stirng is a number """
    try:
        float(value)
        return True
    except ValueError:
        return False

def is_equal(aaa, bbb):
    """ Check if two variables are equal. With type coercion if necessary"""
    if aaa == bbb:
        return True

    if is_number(aaa) and is_number(bbb):
        return float(aaa) == float(bbb)

    return False

def get_extracted(ele, extract):
    """Extract the reauired attributes"""
    out = {}
    for attr_name, argument in extract.iteritems():
        out[attr_name] = str(get_argument(ele, argument))

    return out

def most_common(my_list):
    """Find the most common element of the list"""
    counter = {}

    elements = [e for e in my_list if e != None]

    for ele in elements:
        if ele in counter:
            counter[ele] += 1
        else:
            counter[ele] = 1

    order = sorted(counter, key=counter.get, reverse=True)
    if len(order) == 0:
        raise ValueError(str(my_list))
    return order[0], counter[order[0]]

def complies(element, conditions):
    """Check if the element complies with the constraints"""
    for argument, value in conditions.iteritems():
        if get_argument(element, argument) != value:
            return False

    return True

def average(my_list):
    """Compute the average"""
    if len(my_list) == 0:
        return 0

    return sum(my_list) * 1.0 / len(my_list)


def variance(my_list):
    """Compute the Variance"""
    return map(lambda x: (x - average(my_list))**2, my_list)


def stddev(my_list):
    """Compute the standard Deviation"""
    return math.sqrt(average(variance(my_list)))


def median(my_list):
    """Compute the median"""
    my_list = sorted(my_list)
    if len(my_list) < 1:
        return None
    if len(my_list) %2 == 1:
        return my_list[((len(my_list)+1)/2)-1]
    else:
        return float(sum(my_list[(len(my_list)/2)-1:(len(my_list)/2)+1]))/2.0

def mad(my_list):
    """Compute the Median Average Deviation"""
    return median(map(lambda x: abs(x-median(my_list)), my_list))

from ansible.module_utils.basic import *
main()
