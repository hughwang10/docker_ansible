#!/bin/bash

# $1,   dest_dir: "{{ output_folder_remote }}/upgrade/2", the running stack
# $2,   template_file: "{{ os_msptemplate}}", msp_stack.yaml, stack template file name
# $3,   stack_name: "{{ os_stackname }}", stack name in Heat

echo `date` >>$1/remove_volumes.log
echo "Remove volumes for Old VMs Start" >> $1/remove_volumes.log

for file in `ls -t $1/temp/*-vols.yaml`
do

   file=${file##*/}

   file=${file%-vols.yaml}

   echo "the current VM is $file" >>$1/remove_volumes.log

   #Okay, we know which VM
   #Remove Volumes of old VMs -- all other VMs
   #For TS VM, we still need to keep the uc_ts_* volume, which is using by the new VMs.

   vm_type=${file%-*}

   if [ "$vm_type" == "ts" ]; then

      echo "Keep uc_ts_* volume" >> $1/remove_volumes.log
      sed -n '/.uc_volume_[a-zA-Z0-9_.-]*:/,/^$/p' > $1/temp/$file-vols.yaml.uc $1/temp/$file-vols.yaml

      rm $1/temp/$file-vols.yaml

      if [ -f "$1/temp/$file.yaml" ]; then
         cat $1/temp/$file.yaml $1/temp/$file-vols.yaml.uc > $1/temp/$file.yaml.uc
         rm $1/temp/$file-vols.yaml.uc
         rm $1/temp/$file.yaml
      else
         mv $1/temp/$file-vols.yaml.uc $1/temp/$file.yaml.uc
      fi

      mv $1/temp/$file.yaml.uc $1/temp/$file.yaml

   else
      echo "Remove the old volume file directly" >> $1/remove_volumes.log
      rm $1/temp/$file-vols.yaml
   fi

   #Trigger Heat Stack-Updte
   echo "Trigger stack-update to remove volumes for VM $file" >> $1/remove_volumes.log

   cat $1/temp/*.yaml > $1/$2

   cat $1/$2 >> $1/remove_volumes.log

   heat stack-update -f $1/$2 $3

   sleep 30

   while [[ `heat stack-list | grep -w $3 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
      echo `date` >>$1/remove_volumes.log
      heat stack-list >>$1/remove_volumes.log
      nova list >>$1/remove_volumes.log
      cinder list >>$1/remove_volumes.log
      sleep 10
   done

   echo `date` >>$1/remove_volumes.log
   heat stack-list >>$1/remove_volumes.log

done

echo "Remove volumes of Old VMs  Finished" >> $1/remove_volumes.log

exit 0



