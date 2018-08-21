#!/bin/bash
#
# The script used to do auto rollback all ha groups via MIIT
#
# $1, old_dir: "{{ output_folder_remote_old }}/heat"
# $2, new_dir: "{{ output_folder_remote }}/rollover"
# $3, resource_creation_channel: "{{ resource_creation_channel | default ('0') }}"
# $4, template_file: "{{ os_msptemplate}}"
# $5, stack_name: "{{ os_stackname }}"
# $6, use_heat_env_file: "{{ use_heat_env_ file | default('False') }}"
# $7, cee_dryrun: {{ cee_dryrun | default('False') }}"

echo `date` >>$2/rollover_all_groups.log
echo "rollover all hagroups Start" >> $2/rollover_all_groups.log

for hagroup in `ls -F $1/temp/ | grep "/" | sed 's/.$//'`
do

   echo "hagroup $hagroup"

   echo "hagroup $hagroup" >> $2/rollover_all_groups.log

   #mkdir $2/1/temp
   mkdir $2/1/temp/$hagroup
   rm -f $2/1/temp/$hagroup/*

   # Keep old CP volumes only
   cp $2/../upgrade/1/temp/$hagroup/*.yaml $2/1/temp/$hagroup/

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

   echo `date` >>$2/rollover_all_groups.log
   echo "Rollover/Phase 1 for hagroup $hagroup now"
   echo "Rollover/Phase 1 for hagroup $hagroup now" >>$2/rollover_all_groups.log

   cat $2/1/$4_$hagroup >> $2/rollover_all_groups.log

   # DO NOT trigger heat operation for cee_dryrun mode
   if [[ $7 == "False" ]]; then

      if [[ $6 == "False" ]]; then
         heat stack-update -f $2/1/$4_$hagroup $5_$hagroup
      else
         heat stack-update -f $2/1/$4_$hagroup -e $1/$5_heat_env_file $5_$hagroup
      fi

      sleep 60

      while [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
         echo `date` >> $2/rollover_all_groups.log
         heat stack-list >> $2/rollover_all_groups.log
         nova list >> $2/rollover_all_groups.log
         cinder list >> $2/rollover_all_groups.log
         sleep 10
      done

   fi

   echo `date` >>$2/rollover_all_groups.log
   echo "Rollover/Phase 1 for hagroup $hagroup is done"
   echo "Rollover/Phase 1 for hagroup $hagroup is done" >>$2/rollover_all_groups.log

   #sleep 60

   # Now we start Rollback Phase 2
   #mkdir $2/2/temp
   mkdir $2/2/temp/$hagroup
   rm -f $2/2/temp/$hagroup/*

   echo $2

   cp $1/temp/$hagroup/*.yaml $2/2/temp/$hagroup/

   # special handling needed for MN VM
   # Replace "firstinstall" as "upgrade" for rollback case
   if [ -f "$2/2/temp/$hagroup/mn-01.yaml" ]; then
      sed 's/firstinstall/upgrade/g' $2/2/temp/$hagroup/mn-01.yaml > $2/2/temp/$hagroup/mn-01.yaml.upgrade
      rm -f $2/2/temp/$hagroup/mn-01.yaml
      mv $2/2/temp/$hagroup/mn-01.yaml.upgrade $2/2/temp/$hagroup/mn-01.yaml
   fi

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

   echo `date` >>$2/rollover_all_groups.log
   echo "Rollover/Phase 2 for hagroup $hagroup now"
   echo "Rollover/Phase 2 for hagroup $hagroup now" >>$2/rollover_all_groups.log

   cat $2/2/$4_$hagroup >> $2/rollover_all_groups.log

   # DO NOT trigger heat operation for cee_dryrun mode
   if [[ $7 == "False" ]]; then

      if [[ $6 == "False" ]]; then
         heat stack-update -f $2/2/$4_$hagroup $5_$hagroup
      else
         heat stack-update -f $2/2/$4_$hagroup -e $1/$5_heat_env_file $5_$hagroup
      fi

      sleep 60

      while [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "UPDATE_FAILED" ]] && [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "ROLLBACK_COMPLETE" ]] && [[ `heat stack-list | grep -w $5_$hagroup | awk '{print $6}'` != "ROLLBACK_FAILED" ]]; do
         echo `date` >> $2/rollover_all_groups.log
         heat stack-list >> $2/rollover_all_groups.log
         nova list >> $2/rollover_all_groups.log
         cinder list >> $2/rollover_all_groups.log
         sleep 10
      done
   
   fi

   echo `date` >>$2/rollover_all_groups.log
   echo "Rollover/Phase 2 for hagroup $hagroup is done"
   echo "Rollover/Phase 2 for hagroup $hagroup is done" >>$2/rollover_all_groups.log

   # sleep 60
   # goto next hagroup

done

echo `date` >> $2/rollover_all_groups.log
heat stack-list >> $2/rollover_all_groups.log

echo "Rollback all hagroups Finished" >> $2/rollover_all_groups.log

exit 0



