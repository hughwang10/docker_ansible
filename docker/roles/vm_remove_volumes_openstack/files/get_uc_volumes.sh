#!/bin/bash

# $1,   dest_dir: "{{ output_folder_remote }}", the running stack
# $2,   hagroup: " {{ hagroup }}"
for file in `ls -t $1/upgrade/2/temp/$2/*-vols.yaml`
do

   file=${file##*/}

   file=${file%-vols.yaml}

   #Okay, we know which VM
   #Remove Volumes of old VMs -- all other VMs
   #For TS VM, we still need to keep the uc_ts_* volume, which is using by the new VMs.

   vm_type=${file%-*}

   if [ "$vm_type" == "ts" ]; then

      sed -n '/.uc_volume_[a-zA-Z0-9_.-]*:/,/^$/p' > $1/upgrade/2/temp/$2/$file-vols.yaml.uc $1/upgrade/2/temp/$2/$file-vols.yaml

      #rm $1/temp/$file-vols.yaml
      cat $1/upgrade/2/temp/$2/$file.yaml $1/upgrade/2/temp/$2/$file-vols.yaml.uc > $1/upgrade/2/temp/$2/$file.yaml.uc

      rm $1/upgrade/2/temp/$2/$file-vols.yaml.uc
      rm $1/upgrade/2/temp/$2/$file.yaml
      mv $1/upgrade/2/temp/$2/$file.yaml.uc $1/upgrade/2/temp/$2/$file.yaml

      # for further upgrade
      cp $1/upgrade/2/temp/$2/$file.yaml $1/heat/temp/$2/

   fi

done



