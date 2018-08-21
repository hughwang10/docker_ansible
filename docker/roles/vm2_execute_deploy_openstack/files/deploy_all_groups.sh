#!/bin/bash
#
# The script used to do auto scaling deployment via MIIT
#
# $1, source_dir: "{{ output_folder_remote }}/heat"
# $2, resource_creation_channel: "{{ resource_creation_channel | default ('0') }}"
# $3, template_file: "{{ os_msptemplate}}"
# $4, stack_name: "{{ os_stackname }}"
# $5, heat_rollback: {{ heat_rollback | defautl('False') }}
# $6, use_heat_env_file: {{ use_heat_env_file | default('False') }}
# $7, cee_dryrun: {{ cee_dryrun | default('False') }}

echo `date` >>$1/deploy_all_groups.log
echo "Deployment Start" >> $1/deploy_all_groups.log

for hagroup in `ls -F $1/temp/ | grep "/" | sed 's/.$//'`
do

   echo "hagroup $hagroup"

   echo "hagroup $hagroup" >> $1/deploy_all_groups.log

   cat $1/temp/$hagroup/*.yaml > $1/$3_$hagroup.orig

   if [ $2 -ne 0 ]; then

      python $1/depends.py -f $1/$3_$hagroup.orig -o $1/$3_$hagroup.depends -t $2

      mv $1/$3_$hagroup.depends  $1/$3_$hagroup
   else
      mv $1/$3_$hagroup.orig  $1/$3_$hagroup
   fi

   echo `date` >>$1/deploy_all_groups.log
   echo "create stack for hagroup $hagroup now"
   echo "create stack for hagroup $hagroup now" >>$1/deploy_all_groups.log

   cat $1/$3_$hagroup >> $1/deploy_all_groups.log

   # Not kidkoff Heat actions for cee_dryrun case
   if [[ $7 == "False" ]]; then
      if [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` == "CREATE_COMPLETE" ]]; then
         if [[ $6 == "True" ]]; then
            heat stack-update -f $1/$3_$hagroup -e $1/$4_heat_env_file $4_$hagroup 
         else
            heat stack-update -f $1/$3_$hagroup $4_$hagroup
         fi
      elif [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` == "UPDATE_COMPLETE" ]]; then
         if [[ $6 == "True" ]]; then
            heat stack-update -f $1/$3_$hagroup -e $1/$4_heat_env_file $4_$hagroup
         else   
            heat stack-update -f $1/$3_$hagroup $4_$hagroup
         fi
      else
         if [[ $5 == "True" ]]; then
            if [[ $6 == "True" ]]; then
               heat stack-create -f $1/$3_$hagroup -e $1/$4_heat_env_file -r $4_$hagroup
            else
               heat stack-create -f $1/$3_$hagroup -r $4_$hagroup 
            fi
         else
            if [[ $6 == "True" ]]; then
               heat stack-create -f $1/$3_$hagroup -e $1/$4_heat_env_file $4_$hagroup
            else
              heat stack-create -f $1/$3_$hagroup $4_$hagroup 
            fi
         fi
      fi

      sleep 60

      while [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` != "CREATE_COMPLETE" ]] && [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` != "UPDATE_FAILED" ]] && [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` != "CREATE_FAILED" ]] && [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` != "ROLLBACK_COMPLETE" ]] && [[ `heat stack-list | grep -w $4_$hagroup | awk '{print $6}'` != "ROLLBACK_FAILED" ]]; do
         echo `date` >> $1/deploy_all_groups.log
         heat stack-list >> $1/deploy_all_groups.log
         nova list >> $1/deploy_all_groups.log
         cinder list >> $1/deploy_all_groups.log
         sleep 10
      done
   fi

   echo `date` >>$1/deploy_all_groups.log
   echo "create stack for hagroup $hagroup is done"
   echo "create stack for hagroup $hagroup is done" >>$1/deploy_all_groups.log

done

echo `date` >> $1/deploy_all_groups.log

if [[ $7 == "False" ]]; then
   heat stack-list >> $1/deploy_all_groups.log
fi

echo "Deployment Finished" >> $1/deploy_all_groups.log

exit 0


