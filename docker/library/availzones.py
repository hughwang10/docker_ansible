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
from novaclient.v1_1 import client
import yaml
import math
import os

def free_count(nt, busy_hosts, free_hosts):
    services= nt.services.list()
    for service in services:
        if service.binary.startswith('nova-compute') and service.status.startswith('enabled') and service.state.startswith('up'):
            if service.host not in busy_hosts:
                if service.host not in free_hosts:
                    free_hosts.append(service.host)
    free_hosts.sort()
    if len(free_hosts) > 2:
       # Sort hosts list
       for index in range(0, max (0, int((len(free_hosts) - 3)/2))):
         # mix list with hosts from the end
         free_hosts.insert(index*2 + 1,free_hosts.pop()) 

def busy_count(nt, busy_hosts, free_hosts):
    for agg in nt.aggregates.list():
      id=nt.aggregates.get(agg.id).id
      for host in nt.aggregates.get(id).hosts:
        if host not in busy_hosts:
            busy_hosts.append(host)
    busy_hosts.sort()
    if len(busy_hosts) > 2:
       # Sort hosts list
       for index in range(0, max(0, int((len(busy_hosts) - 3)/2))):
         # mix list with hosts from the end
         busy_hosts.insert(index*2 + 1,busy_hosts.pop()) 

def host_addto_zone(myzonename, host, busy_hosts):
      for agg in nt.aggregates.list():
        id=nt.aggregates.get(agg.id).id
        if nt.aggregates.get(id).name==myzonename and host not in nt.aggregates.get(id).hosts:
           nt.aggregates.get(id).add_host(host)
           if host not in busy_hosts:
              busy_hosts.append(host)
           busy_hosts.sort()
           return True
      return False

def incdec(myzonename, incrementor, busy_hosts, free_hosts):
    if incrementor>0:
      for agg in nt.aggregates.list():
        id=nt.aggregates.get(agg.id).id
        if nt.aggregates.get(id).name==myzonename:
            for i in range(0, incrementor):
                if len(free_hosts)>0:
                    host=free_hosts.pop()
                    nt.aggregates.get(id).add_host(host)
                    if host not in busy_hosts:
                        busy_hosts.append(host)
                else:
                    module.fail_json(msg="Could not allocate requested hosts")
    if incrementor<0:
      count=0
      for agg in nt.aggregates.list():
        id=nt.aggregates.get(agg.id).id
        if nt.aggregates.get(id).name==myzonename:
            for host in nt.aggregates.get(id).hosts:
                if count<(-incrementor):
                    nt.aggregates.remove_host(id,host)
                    count+=1
    return True

def zoneadd(nt, myzonename):
    myink=False
    for agg in nt.aggregates.list():
       id=nt.aggregates.get(agg.id).id
       if nt.aggregates.get(id).name==myzonename:
         myink=True
    if not myink:
      nt.aggregates.create(myzonename, myzonename)

def log_aggregates(nt, debug):
    tbuff=[]
    buff=[]
    buff.append('Zones: ')
    if debug:
      for agg in nt.aggregates.list():
        name=nt.aggregates.get(agg).name
        buff.append(name + " : Atlashost: " + get_atlas_host(nt, "Atlas"))
        buff.append(nt.aggregates.get(agg).hosts)
      tbuff.append(buff) 
    return tbuff

def log_hosts(nt, debug):
    tbuff=[]
    tbuff.append('All hosts: ')
    if debug:
      for hyp in nt.hypervisors.list():
        name=nt.hypervisors.get(hyp).hypervisor_hostname
        tbuff.append(name)
    return tbuff

def get_atlas_host(nt,atlas_name):
    instances=nt.servers.list()
    atlashost=''
    if atlas_name=='':
        atlas_name='atlas'
    for instance in instances:
      if atlas_name.lower() in (getattr(instance, 'name')).lower():
        atlashost=getattr(instance,  'OS-EXT-SRV-ATTR:host' )
    return atlashost

def avail_zones_count(nt, availzones):
#    tbuff=[]
    for agg in nt.aggregates.list():
      id=nt.aggregates.get(agg.id).id
      name=nt.aggregates.get(id).name
      for host in nt.aggregates.get(id).hosts:
         if name in availzones.keys():
            availzones[name]+=1
         else:
            availzones[name]=1
#      tbuff.append(name + '_X: ' + str(availzones[name]))
#    return tbuff

def updater(busy_hosts, availzones, wanted):
    for k,v in wanted.iteritems():
        if  k in availzones.keys():
            change=int(math.ceil(wanted[k]))-availzones[k]
        else:
            change=int(math.ceil(wanted[k]))
        incdec(k, change, busy_hosts, free_hosts)

def granger(vms, nt, busy_hosts, free_hosts, availzones, wanted):
    has_hagroup=False
    ts_wanted = dict()
    slb_wanted = dict()
    vom_wanted = dict()
    ts_slb_vom_wanted = dict()
    for vms_item in vms:
        vms_per_host=1
        if  vms_item.has_key('vms_per_host'):
            vms_per_host=int(vms_item['vms_per_host'])
        if vms_item['vm_type']  in ['ts']:
            if vms_item.has_key('hagroup'):
                has_hagroup=True
                zoneadd(nt, vms_item['hagroup'])
                if  vms_item['hagroup'] in ts_wanted.keys():
                    ts_wanted[vms_item['hagroup']]+=float(vms_item['vm_end_number'])/float(vms_per_host)
                else:
                    ts_wanted[vms_item['hagroup']]=float(vms_item['vm_end_number'])/float(vms_per_host)
        elif vms_item['vm_type']  in ['slb']:
            if vms_item.has_key('hagroup'):
                has_hagroup=True
                zoneadd(nt, vms_item['hagroup'])
                if  vms_item['hagroup'] in slb_wanted.keys():
                    slb_wanted[vms_item['hagroup']]+=float(vms_item['vm_end_number'])/float(vms_per_host)
                else:
                    slb_wanted[vms_item['hagroup']]=float(vms_item['vm_end_number'])/float(vms_per_host)
        elif vms_item['vm_type']  in ['vom']:
            if vms_item.has_key('hagroup'):
                has_hagroup=True
                zoneadd(nt, vms_item['hagroup'])
                if  vms_item['hagroup'] in vom_wanted.keys():
                    vom_wanted[vms_item['hagroup']]+=float(vms_item['vm_end_number'])/float(vms_per_host)
                else:
                    vom_wanted[vms_item['hagroup']]=float(vms_item['vm_end_number'])/float(vms_per_host)
        elif vms_item['vm_type'] not in ['mn', 'mon', 'ddc']:
            if vms_item.has_key('hagroup'):
                has_hagroup=True
                zoneadd(nt, vms_item['hagroup'])
                if  vms_item['hagroup'] in wanted.keys():
                    wanted[vms_item['hagroup']]+=float(vms_item['vm_end_number'])/float(vms_per_host)
                else:
                    wanted[vms_item['hagroup']]=float(vms_item['vm_end_number'])/float(vms_per_host)
    for k,v in ts_wanted.iteritems():
        if  k in ts_slb_vom_wanted.keys():
            if v>ts_slb_vom_wanted[k]:
                ts_slb_vom_wanted[k]=v
        else:
            ts_slb_vom_wanted[k]=v
    for k,v in slb_wanted.iteritems():
        if  k in ts_slb_vom_wanted.keys():
            if v>ts_slb_vom_wanted[k]:
                ts_slb_vom_wanted[k]=v
        else:
            ts_slb_vom_wanted[k]=v
    for k,v in vom_wanted.iteritems():
        if  k in ts_slb_vom_wanted.keys():
            if v>ts_slb_vom_wanted[k]:
                ts_slb_vom_wanted[k]=v
        else:
             ts_slb_vom_wanted[k]=v
    for k,v in ts_slb_vom_wanted.iteritems():
        has_hagroup=True
        if k in wanted.keys():
            wanted[k]+=float(v)
        else:
            wanted[k]=float(v)
    return has_hagroup


module = AnsibleModule(
    argument_spec = dict(
       ha_zone=dict(required=True, type='str'),
       compute_hosts_in_ha_zone=dict(required=True, type='str'),
       ddc_zone=dict(required=True, type='str'),
       number_of_ddc_cabinet=dict(required=True, type='str'),
       compute_hosts_in_ddc_zone=dict(required=True, type='str'),
       traffic_zone=dict(required=True, type='str'),
       force_traffic_zone=dict(required=True, type='str'),
       vms_json=dict(required=True, type='str'),
       reserved_hosts_json=dict(required=True, type='str'),
       atlas_name=dict(required=True, type='str'),
       os_auth_url=dict(required=True, type='str'),
       os_password=dict(required=True, type='str'),
       os_tenant_name=dict(required=True, type='str'),
       os_username=dict(required=True, type='str'),
       os_debug_mode=dict(default=False, type='bool'),
       dry=dict(default=False, type='bool')
    ),
    supports_check_mode=True
)
debug_buffer=[]
os_debug_mode=False
try:
    ha_zone=module.params.get('ha_zone')
    compute_hosts_in_ha_zone=module.params.get('compute_hosts_in_ha_zone')
    ddc_zone=module.params.get('ddc_zone')
    number_of_ddc_cabinet=module.params.get('number_of_ddc_cabinet')
    compute_hosts_in_ddc_zone=module.params.get('compute_hosts_in_ddc_zone')
    traffic_zone=module.params.get('traffic_zone')
    force_traffic_zone=module.params.get('force_traffic_zone')
    vms_json=module.params.get('vms_json')
    reserved_hosts_json=module.params.get('reserved_hosts_json')
    atlas_name=module.params.get('atlas_name')
    os_auth_url=module.params.get('os_auth_url')
    os_password=module.params.get('os_password')
    os_tenant_name=module.params.get('os_tenant_name')
    os_username=module.params.get('os_username')
    os_debug_mode=module.params.get('os_debug_mode')
    dry=module.params.get('dry')
    nt = client.Client(os_username, os_password, os_tenant_name, os_auth_url)
    debug_buffer.append(log_hosts(nt, os_debug_mode))
    debug_buffer.append(log_aggregates(nt, os_debug_mode))
    atlashost=get_atlas_host(nt,atlas_name)
    busy_hosts=[]
    availzones = dict()
    reserved_hosts = yaml.load(reserved_hosts_json)
    vms = yaml.load(vms_json)
    for host in reserved_hosts:
        if host not in busy_hosts:
            busy_hosts.append(host)
    if atlashost!='' and atlashost not in busy_hosts:
        busy_hosts.append(atlashost)
    free_hosts=[]
    busy_count(nt, busy_hosts, free_hosts)
    wanted = dict()
    non_traffic_hosts=0
    if (int(compute_hosts_in_ha_zone)>0):
        zoneadd(nt, ha_zone)
        if atlashost!='':
            if host_addto_zone(ha_zone, atlashost, busy_hosts):
                non_traffic_hosts-=1
        wanted[ha_zone]=float(compute_hosts_in_ha_zone)
        non_traffic_hosts+=wanted[ha_zone]
    for ddcz in range(1, int(number_of_ddc_cabinet)+1):
        zoneadd(nt, ddc_zone+str(ddcz))
        wanted[ddc_zone+str(ddcz)]=1.0
        non_traffic_hosts+=wanted[ddc_zone+str(ddcz)]
    avail_zones_count(nt, availzones)
    free_count(nt, busy_hosts, free_hosts)
    if force_traffic_zone.startswith('True'):
        zoneadd(nt, traffic_zone)
        free_hosts=[]
        free_count(nt, busy_hosts, free_hosts)
        if len(free_hosts)-non_traffic_hosts>0:
            wanted[traffic_zone]=float(len(free_hosts)-non_traffic_hosts)
    else:
        granger(vms, nt, busy_hosts, free_hosts, availzones, wanted)
    debug_buffer.append(['Busy: '] + busy_hosts + ['Free: '] + free_hosts + ['Availzones: '] + list(availzones.items()) + ['Wanted: '] + list(wanted.items()))
    if not dry:
       updater(busy_hosts, availzones, wanted)

    debug_buffer.append(log_aggregates(nt, os_debug_mode))

except Exception, e:
    exc = {}
    exc['vm_name'] = str(e)
    module.fail_json(**exc)

zonlist = {}
zonlist['vm_name'] = "OK"

if os_debug_mode:
  zonlist['debug'] = debug_buffer
module.exit_json(**zonlist)
