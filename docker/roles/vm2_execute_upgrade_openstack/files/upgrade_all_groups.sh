#!/bin/bash
#
# The script used to do auto upgrade all ha groups via MIIT
#
# $1, old_dir: "{{ output_folder_remote_old }}/heat"
# $2, new_dir: "{{ output_folder_remote }}/upgrade"
# $3, resource_creation_channel: "{{ resource_creation_channel | default ('0') }}"
# $4, template_file: "{{ os_msptemplate}}"
# $5, stack_name: "{{ os_stackname }}"
# $6, use_heat_env_file: " {{ use_heat_env_file | default('False') }}"
# $7, cee_dryrun: "{{ cee_dryrun | default('False') }}"

echo `date` >>$2/upgrade_all_groups.log
echo "Upgrade all hagroups Start" >> $2/upgrade_all_groups.log

for hagroup in `ls -F $1/temp/ | grep "/" | sed 's/.$//'`
do

   echo "hagroup $hagroup"

   echo "hagroup $hagroup" >> $2/upgrade_all_groups.log

   #mkdir $2/1/temp
   mkdir $2/1/temp/$hagroup
   rm -f $2/1/temp/$hagroup/*

   # get old CP volumes
   for file in `ls $1/temp/$hagroup/`
   do
      vm_name=${file%.yaml}
      vm_vols_file=$vm_name-vols.yaml

      echo $vm_vols_file

      sed -rn '/.*_volume_[a-zA-Z0-9_.-]*:/,/^$/p' > $2/1/temp/$hagroup/$vm_vols_file $1/temp/$hagroup/$file
   done

   # remove 0-vols.yaml
   rm -f $2/1/temp/$hagroup/0-vols.yaml

   # copy 0.yaml from $1/temp/$hagroup to $2/1/temp/$hagroup
   cp $1/temp/$hagroup/0.yaml $2/1/temp/$hagroup/

   # assemble orig template file
   cat $2/1/temp/$hagroup/*.yaml > $2/1/$4_$hagroup.orig

   # do we need to add dependency?
   if [ $3 -ne 0 ]; then
      # add dependency
      python $2/1/depends.py -f $2/1/$4_$hagroup.orig -o $2/1/$4_$hagroup.depends -t $3

      # use depends as stack template file
      mv $2/1/$4_$hagroup.depends $2/1/$4_$hagroup
   else
      # use orig as stack template file
      mv $2/1/$4_$hagroup.orig $2/1/$4_$hagroup
   fi

   echo `date` >>$2/upgrade_all_groups.log
   echo "Upgrade/Phase 1 for hagroup $hagroup now"
   echo "Upgrade/Phase 1 for hagroup $hagroup now" >>$2/upgrade_all_groups.log

   cat $2/1/$4_$hagroup >> $2/upgrade_all_groups.log

   # DO NOT trigger heat operation for cee_dryrun mode
   if [[ $7 == "False" ]]; then

      if [[ $6 == "False" ]]; then
         heat stack-update -f $2/1/$4_$hagroup $5_$hagroup
      else
         heat stack-update -f $2/1/$4_$hagroup -e $1/$5_heat_env_file $5_$hagroup
      fi

      sleep 60

      while [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
         echo `date` >> $2/upgrade_all_groups.log
         heat stack-list >> $2/upgrade_all_groups.log
         nova list >> $2/upgrade_all_groups.log
         cinder list >> $2/upgrade_all_groups.log
         sleep 10
      done
   fi

   echo `date` >>$2/upgrade_all_groups.log
   echo "Upgrade/Phase 1 for hagroup $hagroup is done"
   echo "Upgrade/Phase 1 for hagroup $hagroup is done" >>$2/upgrade_all_groups.log

   #sleep 60

   # Now we start Upgrade Phase 2
   #mkdir $2/2/temp
   mkdir $2/2/temp/$hagroup
   rm -f $2/2/temp/$hagroup/*

   echo $2

   cp $2/1/temp/$hagroup/*.yaml $2/2/temp/$hagroup/

   cp $2/../heat/temp/$hagroup/*.yaml $2/2/temp/$hagroup/

   # assemble orig template file
   cat $2/2/temp/$hagroup/*.yaml > $2/2/$4_$hagroup.orig

   # do we need to add dependency?
   if [ $3 -ne 0 ]; then
      # add dependency
      python $2/2/depends.py -f $2/2/$4_$hagroup.orig -o $2/2/$4_$hagroup.depends -t $3

      # use depends as stack template file
      mv $2/2/$4_$hagroup.depends $2/2/$4_$hagroup
   else
      # use orig as stack template file
      mv $2/2/$4_$hagroup.orig $2/2/$4_$hagroup
   fi

   echo `date` >>$2/upgrade_all_groups.log
   echo "Upgrade/Phase 2 for hagroup $hagroup now"
   echo "Upgrade/Phase 2 for hagroup $hagroup now" >>$2/upgrade_all_groups.log

   cat $2/2/$4_$hagroup >> $2/upgrade_all_groups.log

   # DO NOT trigger heat operation for cee_dryrun mode
   if [[ $7 == "False" ]]; then

      if [[ $6 == "False" ]]; then
         heat stack-update -f $2/2/$4_$hagroup $5_$hagroup
      else
         heat stack-update -f $2/2/$4_$hagroup -e $2/../heat/$5_heat_env_file $5_$hagroup
      fi

      sleep 60

      while [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "UPDATE_FAILED" ]] && [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "ROLLBACK_COMPLETE" ]] && [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "ROLLBACK_FAILED" ]]; do
         echo `date` >> $2/upgrade_all_groups.log
         heat stack-list >> $2/upgrade_all_groups.log
         nova list >> $2/upgrade_all_groups.log
         cinder list >> $2/upgrade_all_groups.log
         sleep 10
      done
   fi

   echo `date` >>$2/upgrade_all_groups.log
   echo "Upgrade/Phase 2 for hagroup $hagroup is done"
   echo "Upgrade/Phase 2 for hagroup $hagroup is done" >>$2/upgrade_all_groups.log

   # sleep 60
   # goto next hagroup

done

echo `date` >> $2/upgrade_all_groups.log
heat stack-list >> $2/upgrade_all_groups.log

echo "Upgrade all hagroups Finished" >> $2/upgrade_all_groups.log

exit 0



