#!/bin/bash
#
# The script used to do auto scaling deployment via MIIT
#
# $1,  source_dir: "{{ output_folder_remote }}/heat"
# $2, dest_dir: "{{ output_folder_remote }}/scaling"
# $3, vms: "{{ vms_per_batch | default(2) }}"
# $4, template_file: "{{ os_msptemplate}}"
# $5, stack_name: "{{ os_stackname }}"
# $6, expand_site_mode: " {{ expand_site | default('False') }}

count=0

echo `date` >>$2/scaling.log
echo "Scaling Deployment Start" >> $2/scaling.log

# Check if expand_site mode
if [ "$6" = "True" ]; then

   echo "expand_site mode is true" >> $2/scaling.log
 
   for file in `ls -tr $1/temp`
   do
      if [ -f "$2/temp/$file" ]; then
         echo "remove $1/temp/$file, $2/temp/$file already exists" >> $2/scaling.log
         rm $1/temp/$file     
      fi
   done
fi

for file in `ls -tr $1/temp`
do

   echo "copy $1/temp/$file to dir $2/temp/" >>$2/scaling.log

   cp $1/temp/$file $2/temp/

   let "count=$count+1"

   p=`expr $count % $3`

   if [ $p -eq 0 ]; then

      cat $2/temp/*.yaml > $2/$4

      cat $2/$4 >>$2/scaling.log

      echo `date` >>$2/scaling.log
      echo "update the stack now" >>$2/scaling.log

      if [[ `heat stack-list | grep $5 | awk '{print $6}'` == "CREATE_COMPLETE" ]]; then
         heat stack-update -f $2/$4 $5
      elif [[ `heat stack-list | grep $5 | awk '{print $6}'` == "UPDATE_COMPLETE" ]]; then
         heat stack-update -f $2/$4 $5
      else
         heat stack-create -f $2/$4 -r $5
      fi

      sleep 60

      while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep $5 | awk '{print $6}'` != "CREATE_COMPLETE" ]]; do
         echo `date` >>$2/scaling.log
         heat stack-list >>$2/scaling.log
         nova list >>$2/scaling.log
         cinder list >>$2/scaling.log
         sleep 10
      done

      echo `date` >>$2/scaling.log
      heat stack-list >>$2/scaling.log

   fi

done

p=`expr $count % $3`

if [ $p -ne 0 ]; then

   cat $2/temp/*.yaml > $2/$4

   cat $2/$4 >>$2/scaling.log

   echo `date` >>$2/scaling.log
   echo "update the stack now" >>$2/scaling.log

   if [[ `heat stack-list | grep $5 | awk '{print $6}'` == "CREATE_COMPLETE" ]]; then
      heat stack-update -f $2/$4 $5
   elif [[ `heat stack-list | grep $5 | awk '{print $6}'` == "UPDATE_COMPLETE" ]]; then
      heat stack-update -f $2/$4 $5
   else
      heat stack-create -f $2/$4 -r $5
   fi

   sleep 60

   while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep $5 | awk '{print $6}'` != "CREATE_COMPLETE" ]]; do
      echo `date` >>$2/scaling.log
      heat stack-list >>$2/scaling.log
      nova list >>$2/scaling.log
      cinder list >>$2/scaling.log
      sleep 10
   done

fi

echo `date` >>$2/scaling.log
heat stack-list >>$2/scaling.log

echo "Scaling Deployment Finished" >> $2/scaling.log

exit 0



