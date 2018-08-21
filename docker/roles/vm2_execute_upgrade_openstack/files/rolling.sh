#!/bin/bash

# $1,   source_dir: "{{ output_folder_remote }}/heat" 
# $2,   dest_dir: "{{ output_folder_remote }}/upgrade"
# $3,   vm_name, per the order in hosts_vmnames 
# $4,   template_file: "{{ os_msptemplate}}" 
# $5,   stack_name: "{{ os_stackname }}"

echo "Rolling Update for $3 is start" >> $2/2/upgrade.log

echo "Running stack template file is:"

cat $2/0/$4 >>$2/2/upgrade.log

echo "Old VM is still running, Create New VM Root Volume, for $3" >> $2/2/upgrade.log

cp $2/1.5/temp/$3-vols.yaml $2/2/temp/

cat $2/2/temp/*.yaml > $2/2/$4

cat $2/2/$4 >>$2/2/upgrade.log

echo `date` >>$2/2/upgrade.log
echo "update the stack now" >>$2/2/upgrade.log

heat stack-update -f $2/2/$4 $5

sleep 60

while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
   echo `date` >>$2/2/upgrade.log
   heat stack-list >>$2/2/upgrade.log
   nova list >>$2/2/upgrade.log
   cinder list >>$2/2/upgrade.log
   sleep 10
done

echo `date` >>$2/2/upgrade.log
heat stack-list >>$2/2/upgrade.log

echo "Kill the old VM, but keep it volumes, for $3" >> $2/2/upgrade.log

rm $2/2/temp/$3.yaml
rm $2/2/temp/$3-vols.yaml 
cp $2/1/temp/$3-vols.yaml $2/2/temp/
cp $2/1.5/temp/$3-vols.yaml $2/2/temp/$3.yaml

cat $2/2/temp/*.yaml > $2/2/$4

cat $2/2/$4 >>$2/2/upgrade.log

echo `date` >>$2/2/upgrade.log
echo "update the stack now" >>$2/2/upgrade.log

heat stack-update -f $2/2/$4 $5

sleep 30

while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
   echo `date` >>$2/2/upgrade.log
   heat stack-list >>$2/2/upgrade.log
   nova list >>$2/2/upgrade.log
   cinder list >>$2/2/upgrade.log
   sleep 10
done

echo `date` >>$2/2/upgrade.log
heat stack-list >>$2/2/upgrade.log

echo "Create new VM for $3" >> $2/2/upgrade.log

rm $2/2/temp/$3.yaml
cp $1/temp/$3.yaml $2/2/temp

cat $2/2/temp/*.yaml > $2/2/$4

cat $2/2/$4 >>$2/2/upgrade.log

echo `date` >>$2/2/upgrade.log
echo "update the stack now" >>$2/2/upgrade.log

heat stack-update -f $2/2/$4 $5

sleep 30

while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
   echo `date` >>$2/2/upgrade.log
   heat stack-list >>$2/2/upgrade.log
   nova list >>$2/2/upgrade.log
   cinder list >>$2/2/upgrade.log
   sleep 10
done

echo `date` >>$2/2/upgrade.log
heat stack-list >>$2/2/upgrade.log

echo "Rolling Update for $3 is done" >> $2/2/upgrade.log
 
exit 0

