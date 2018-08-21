import sys

def xparam4 (vm,
             ipaddr):
    returnvalue=' - vm_type: ' + vm['vm_type'] +'\n'
    returnvalue+='   vm_basename: ' + vm['vm_type']+'-\n'
    returnvalue+='   vm_numbers: ' + vm['vm_numbers'] + '\n'
    returnvalue+='   vm_end_number: ' + '"{{ ('+vm['vm_type']+'_number | default(' + str(vm['increment']) + ')) | int  }}"' + '\n'
    returnvalue+='   ip_start_offset: '+ str(ipaddr) + '\n'
    if 'execution_host_index_start' in vm:
        returnvalue+='   execution_host_index_start: ' + str(vm['execution_host_index_start']) + '\n'
    if 'hagroup' in vm:
        returnvalue+='   hagroup: '+ vm['hagroup'] + '\n'
    return returnvalue

sitespec1='''---
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

'''
allvms={'jeos', 'tools', 'mn', 'mon', 'ddc', 'slb', 'vom', 'dk', 'ts' , 'da','cim','custom'}

kind=''

if len(sys.argv)>1:
	kind=sys.argv[1]
increment=1
if '4' in kind:
	increment=4
if '8' in kind:
	increment=40
truevms=[]

truevms.append({'vm_type':'mn',     'increment':1, 'vm_numbers':'[1]', 'hagroup':'mgmt_1'})
truevms.append({'vm_type':'mon',    'increment':1, 'vm_numbers':'[1]', 'hagroup':'mgmt_1'})
if 'dz' in kind:
	truevms.append({'vm_type':'ddc',    'increment':3, 'vm_numbers':'[11]', 'hagroup':'ddc_1', 'execution_host_index_start': 1 })
	truevms.append({'vm_type':'ddc',    'increment':3, 'vm_numbers':'[21]', 'hagroup':'ddc_2', 'execution_host_index_start': 1 })
	truevms.append({'vm_type':'ddc',    'increment':3, 'vm_numbers':'[31]', 'hagroup':'ddc_3', 'execution_host_index_start': 1 })
else:
	truevms.append({'vm_type':'ddc',    'increment':2,'vm_numbers':'[1]', 'hagroup':'ddc_1'})
if '4' in kind or '8' in kind:
	truevms.append({'vm_type':'slb',    'increment':increment, 'vm_numbers':'[1]', 'hagroup':'traffic_1'})
	truevms.append({'vm_type':'vom',    'increment':increment, 'vm_numbers':'[1]', 'hagroup':'traffic_1'})
	truevms.append({'vm_type':'ts' ,    'increment':increment, 'vm_numbers':'[1,11,21,31]', 'hagroup':'traffic_1'})
if 'da' in kind:
	truevms.append({'vm_type':'da',     'increment':1, 'vm_numbers':'[1]', 'hagroup':'diameter_1'})
	truevms.append({'vm_type':'cim',    'increment':2, 'vm_numbers':'[1]', 'hagroup':'diameter_1'})
	truevms.append({'vm_type':'custom', 'increment':1, 'vm_numbers':'[1]' })

for vmtype in allvms:
	vflag=True
	for vm in iter(truevms):
		if vm['vm_type']==vmtype:
			vflag=False
	if vflag:
		sitespec1+='create_'+vmtype+'_template: False\n'
for vm in iter(truevms):
    sitespec1+='create_'+vm['vm_type']+'_template: True\n'
ipaddr=3

sitespec1+='''
authusername: admin
authpasswd: wapwap12
lang_list: '{"en":"English"}'
lighttpd_user: admin
# Internal network address for MN
start_ip: '''+str(ipaddr)
sitespec1+='''
oam_start_ip: '''+str(ipaddr)
sitespec1+='''
internal_start_ip: "{{ start_ip }}"
internet_start_ip: "{{ start_ip }}"
access_start_ip: "{{ start_ip }}"
internetingress_start_ip: "{{ start_ip }}"
accessingress_start_ip: "{{ start_ip }}"
controlplanesig_start_ip: "{{ start_ip }}"
msa_sub_ip: "{{ internal_start_ip }}"
mn_sub_ip: "{{ oam_start_ip }}"
clusterid: root'''
#sitespec1+='''# Google DNS IPs, should be replaced
#dns_ips: [ "8.8.4.4", "8.8.8.8" ]'''
sitespec1+='''snmptrap_ip: 127.0.0.1
snmp_port: 162
# Rela license server IP to be configured
licenseserver_ip: "https://127.0.0.1:8443/YPServer"
'''
#sitespec1+='''#licenseserver_ip: "https://esesslx0385.ss.sw.ericsson.se:8443/YPServer"
#'''

if 'dz' in kind:
	sitespec1+='number_of_ddc_cabinet: 3\n'
else:
	sitespec1+='number_of_ddc_cabinet: 0\n'

sitespec1+='vms:\n'
for vm in iter(truevms):
    sitespec1+=xparam4(vm, ipaddr)
    ipaddr+=vm['increment']
print sitespec1,
