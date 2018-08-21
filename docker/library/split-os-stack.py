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
#from ansible.module_utils.basic import *
import yaml
import sys
import copy

def check_has_htype(dictva, htypes):
    if type(dictva['type']) is str and dictva['type'] in htypes:
        return True
    return False

def MoveResource(resource_common, resource, selects):
    for k, v in resource_common.items():
        uncommon=False
        for selection in selects:
            if 'r_type' in selection and check_has_htype(v, selection['r_type']):
                if not 'in_key' in selection and not 'not_key' in selection:
                    uncommon=True
                    break
                elif 'in_key' in selection and not 'not_key' in selection:
                    if selection['in_key'] in k:
                        uncommon=True
                        break
                elif not 'in_key' in selection and 'not_key' in selection:
                    if not selection['not_key'] in k:
                        uncommon=True
                        break
            elif not 'r_type' in selection :
                if 'in_key' in selection and not 'not_key' in selection:
                    if selection['in_key'] in k:
                        uncommon=True
                        break
                elif not 'in_key' in selection and 'not_key' in selection:
                    if not selection['not_key'] in k:
                        uncommon=True
                        break

        if uncommon and type(v) is dict:
            resource[k]=copy.deepcopy(v)
            del resource_common[k]

#-----------------------------------------------------------------------------------------

resource_sets=[]
selections=[]
if len(sys.argv)<3:
    print "syntax error need 2 arguments"
    print "Example:"
    print "python",sys.argv[0], "mspstack.yaml any_volumes"
    exit()

filter=(sys.argv[2])
if 'server_no_port_externals' in filter:
    selections.append([{ 'r_type': ['OS::Nova::Server']}, { 'r_type': ['Ericsson::Neutron::Port'], 'not_key' : 'external' }])
if 'any_Ericsson_flavors' in filter:
    selections.append([{ 'r_type': ['Ericsson::Nova::Flavor'] }])
if 'any_volumes_with_flavors' in filter:
    selections.append([{ 'r_type': ['OS::Cinder::Volume', 'file:///home/atlasadm/flavor.yaml', 'flavor.yaml']}])
if 'any_volumes' in filter:
    selections.append([{ 'r_type': ['OS::Cinder::Volume']}])
if 'any_nets' in filter:
    selections.append([{ 'r_type': ['OS::Neutron::Net'] }])
if 'any_routers' in filter:
    selections.append([{ 'r_type': ['OS::Neutron::Router'] }])
if 'any_routerinterfaces' in filter:
    selections.append([{ 'r_type': ['Ericsson::Neutron::RouterInterface'] }])
if 'any_os_routerinterfaces' in filter:
    selections.append([{ 'r_type': ['OS::Neutron::RouterInterface'] }])
if 'any_subnets' in filter:
    selections.append([{ 'r_type': ['OS::Neutron::Subnet'] }])
if 'any_servers' in filter:
    selections.append([{ 'r_type': ['OS::Nova::Server'] }])
if 'any_server_or_ports' in filter:
    selections.append([{ 'r_type': ['OS::Nova::Server'] },{ 'r_type': ['Ericsson::Neutron::Port'] }])
if 'any_networks' in filter:
    selections.append([{ 'r_type': ['file:///home/atlasadm/network.yaml', 'network.yaml'] }])
if 'any_network_pools' in filter:
    selections.append([{ 'r_type': ['file:///home/atlasadm/network_pool.yaml', 'network_pool.yaml'] }])
if 'any_port_not_externals' in filter:
    selections.append([{ 'r_type': ['Ericsson::Neutron::Port'], 'not_key' : 'external' }])
if 'any_port_externals' in filter:
    selections.append([{ 'r_type': ['Ericsson::Neutron::Port'], 'in_key' : 'external' }])
print "Filtering with these selections:"
print selections
file_name=sys.argv[1]
file_name=file_name.replace('.yaml','')
infile_name=file_name+'.yaml'
infile=open(infile_name,'r')

mspservers = yaml.load(infile)
infile.close()

the_resources=mspservers['resources']

header={'heat_template_version': '2013-05-23',
        'description': 'HOT template for deploying the MSP application',
        'resources': {}}

for icount in xrange(len(selections)+1):
    resource_sets.append(header)

resource_sets[0]=copy.deepcopy(mspservers)

for icount in xrange(len(selections)):
    MoveResource(resource_sets[0]['resources'], resource_sets[icount+1]['resources'], selections[icount])


for icount in xrange(len(selections)+1):
    with open(file_name+'-'+"%02d" % (icount)+'.yaml', 'w') as outfile:
        yaml.dump(resource_sets[icount], outfile, default_flow_style=False)
    outfile.close()
