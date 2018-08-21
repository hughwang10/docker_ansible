#!/bin/bash

# $1,   source_dir: "{{ output_folder_remote }}/upgrade/0", the old stack before upgrade
# $2,   dest_dir: "{{ output_folder_remote }}/upgrade/2", the running stack (failure point)
# $3,   rollover_dir: "{{ output_folder_remote }}/rollover/2"
# $4,   template_file: "{{ os_msptemplate}}", msp_stack.yaml, stack template file name
# $5,   stack_name: "{{ os_stackname }}", stack name in Heat

echo `date` >>$3/rollover.log
echo "Rollover for Rolling Upgrade Start" >> $3/rollover.log

for file in `ls -t $2/temp/*-vols.yaml`
do

   file=${file##*/}

   file=${file%-vols.yaml}

   echo "the last upgrading VM is $file" >>$3/rollover.log

   #Okay we know the last upgrading VM BEFORE rollback
   echo "Kill new VM and its volumes, also keep old VM volumes" >>$3/rollover.log

   rm $2/temp/$file.yaml
   rm $2/temp/$file-vols.yaml

   cp $1/../1/temp/$file-vols.yaml $2/temp/

   cat $2/temp/*.yaml > $2/$4

   cat $2/$4 >>$3/rollover.log

   echo `date` >>$3/rollover.log
   echo "update the stack now" >>$3/rollover.log

   heat stack-update -f $2/$4 $5

   sleep 30

   while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
      echo `date` >>$3/rollover.log
      heat stack-list >>$3/rollover.log
      nova list >>$3/rollover.log
      cinder list >>$3/rollover.log
      sleep 10
   done

   echo `date` >>$3/rollover.log
   heat stack-list >>$3/rollover.log


   echo "Re-create old VM, based on the exist volumes" >>$3/rollover.log

   rm $2/temp/$file-vols.yaml

   cp $1/temp/$file.yaml $2/temp/

   cat $2/temp/*.yaml > $2/$4

   cat $2/$4 >>$3/rollover.log

   echo `date` >>$3/rollover.log
   echo "update the stack now" >>$3/rollover.log

   heat stack-update -f $2/$4 $5

   sleep 30

   while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
      echo `date` >>$3/rollover.log
      heat stack-list >>$3/rollover.log
      nova list >>$3/rollover.log
      cinder list >>$3/rollover.log
      sleep 10
   done

   echo `date` >>$3/rollover.log
   heat stack-list >>$3/rollover.log


done

echo "Rollover for Rolling Upgrade Finished" >> $3/rollover.log

exit 0


