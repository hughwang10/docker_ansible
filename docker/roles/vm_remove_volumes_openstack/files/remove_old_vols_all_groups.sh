#!/bin/bash
#
# The script used to do auto rollback all ha groups via MIIT
#
# $1, new_dir: "{{ output_folder_remote }}/"
# $2, resource_creation_channel: "{{ resource_creation_channel | default ('0') }}"
# $3, template_file: "{{ os_msptemplate}}"
# $4, stack_name: "{{ os_stackname }}"
# $5, use_heat_env_file: "{{ use_heat_env_file | default('False') }}"
# $6, cee_dryrun: " {{ cee_dryrun | default('False') }}"

echo `date` >>$1/upgrade/remove_old_vols_all_groups.log
echo "remove old volumes for all hagroups Start" >> $1/upgrade/remove_old_vols_all_groups.log

for hagroup in `ls -F $1/upgrade/2/temp/ | grep "/" | sed 's/.$//'`
do

   echo "hagroup $hagroup"

   echo "hagroup $hagroup" >> $1/upgrade/remove_old_vols_all_groups.log

   $1/upgrade/2/get_uc_volumes.sh $1 $hagroup

   rm -f $1/upgrade/2/temp/$hagroup/*-vols.yaml

   # assemble orig template file
   cat $1/upgrade/2/temp/$hagroup/*.yaml > $1/upgrade/2/$3_$hagroup.orig

   # do we need to add dependency?
   if [ $2 -ne 0 ]; then
      # add dependency
      python $1/upgrade/2/depends.py -f $1/upgrade/2/$3_$hagroup.orig -o $1/upgrade/2/$3_$hagroup.depends -t $2

      # use depends as stack template file
      mv $1/upgrade/2/$3_$hagroup.depends $1/upgrade/2/$3_$hagroup
   else
      # use orig as stack template file
      mv $1/upgrade/2/$3_$hagroup.orig $1/upgrade/2/$3_$hagroup
   fi

   echo `date` >>$1/upgrade/remove_old_vols_all_groups.log
   echo "Remove old volumes for hagroup $hagroup now"
   echo "Remove old volumes for hagroup $hagroup now" >>$1/upgrade/remove_old_vols_all_groups.log

   cat $1/upgrade/2/$3_$hagroup >> $1/upgrade/remove_old_vols_all_groups.log

   # DO NOT trigger heat operation for cee_dryrun mode
   if [[ $6 == "False" ]]; then

      if [[ $5 == "False" ]]; then
         heat stack-update -f $1/upgrade/2/$3_$hagroup $4_$hagroup
      else
         heat stack-update -f $1/upgrade/2/$3_$hagroup -e $1/heat/$4_heat_env_file $4_$hagroup 
      fi

      sleep 60

      while [[ `heat stack-list | grep $4_$hagroup | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
         echo `date` >> $1/upgrade/remove_old_vols_all_groups.log
         heat stack-list >> $1/upgrade/remove_old_vols_all_groups.log
         nova list >> $1/upgrade/remove_old_vols_all_groups.log
         cinder list >> $1/upgrade/remove_old_vols_all_groups.log
         sleep 10
      done
  
   fi

   # sleep 60
   # goto next hagroup

   echo `date` >>$1/upgrade/remove_old_vols_all_groups.log
   echo "Remove old volumes for hagroup $hagroup is done"
   echo "Remove old volumes for hagroup $hagroup is done" >>$1/upgrade/remove_old_vols_all_groups.log

done

echo `date` >> $1/upgrade/remove_old_vols_all_groups.log
heat stack-list >> $1/upgrade/remove_old_vols_all_groups.log

echo "Remove old volumes for all hagroups Finished" >> $1/upgrade/remove_old_vols_all_groups.log

exit 0

