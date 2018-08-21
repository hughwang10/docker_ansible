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
import yaml
import sys

def find_any_alias(dictvalue,any):
    for k, v in dictvalue.items():
        if type(v) is str:
            if k == any:
                return v.strip()
    return ''

def find_any_alias_properties(dictvalue, any):
    for k, v in dictvalue.items():
        if type(v) is dict:
            if k=='properties':
                return find_any_alias(v,any+"name")
    return ''

def get_type_aliases(dictvalue, any):
    tmp_aliases={}
    for k, v in dictvalue.items():
        adictvalue={}
        the_type=v['type']
        if type(v) is dict:
            found_alias=find_any_alias_properties(v,any)
        if found_alias!='':
            adictvalue[k]=found_alias
            if the_type in tmp_aliases:
                tmp_aliases[the_type].append(adictvalue)
            else:
                tmp_aliases[the_type]=[adictvalue]
    the_sum=0
    return tmp_aliases


#-----------------------------------------------------------------------------------------

type_aliases={}
resource_sets=[]

infile_name=sys.argv[1]
infile=open(infile_name,'r')
mspservers = yaml.load(infile)
infile.close()

the_resources=mspservers['resources']
type_aliases['typeless']=get_type_aliases(the_resources,'')
for atype in ['net','flavor','subnet']:
    type_aliases[atype]=get_type_aliases(the_resources,atype+'_')
with open('aliases.yaml', 'w') as outfile:
    yaml.dump(type_aliases, outfile, default_flow_style=False)
outfile.close

