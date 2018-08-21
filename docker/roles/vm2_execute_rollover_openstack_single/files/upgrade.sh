#!/bin/bash

# $1,   source_dir: "{{ output_folder_remote }}/heat" 
# $2,   dest_dir: "{{ output_folder_remote }}/upgrade/2" 
# $3,   vms: "{{ vms_per_batch | default(2) }}" 
# $4,   template_file: "{{ os_msptemplate}}" 
# $5,   stack_name: "{{ os_stackname }}"

count=0

echo `date` >>$2/upgrade.log
echo "Scaling Deployment Start" >> $2/upgrade.log

for file in `ls -tr $1/temp`
do

   echo "copy $1/temp/$file to dir $2/temp/" >>$2/upgrade.log

   cp $1/temp/$file $2/temp/

   let "count=$count+1"
 
   p=`expr $count % $3`        
  
   if [ "$p" = "0" ]; then
      
      cat $2/temp/*.yaml > $2/$4

      cat $2/$4 >>$2/upgrade.log

      echo `date` >>$2/upgrade.log
      echo "update the stack now" >>$2/upgrade.log
      
      heat stack-update -f $2/$4 $5

      sleep 60

      while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do 
         echo `date` >>$2/upgrade.log
         heat stack-list >>$2/upgrade.log
         nova list >>$2/upgrade.log
         cinder list >>$2/upgrade.log
         sleep 10 
      done

   echo `date` >>$2/upgrade.log
   heat stack-list >>$2/upgrade.log
      
 
   fi

done

p=`expr $count % $3`        
  
if [ "$p" != "0" ]; then
      
   cat $2/temp/*.yaml > $2/$4

   cat $2/$4 >>$2/upgrade.log

   echo `date` >>$2/upgrade.log
   echo "update the stack now" >>$2/upgrade.log

   heat stack-update -f $2/$4 $5

   sleep 60

   while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]]; do
      echo `date` >>$2/upgrade.log
      heat stack-list >>$2/upgrade.log
      nova list >>$2/upgrade.log
      cinder list >>$2/upgrade.log
      sleep 10 
   done

   echo `date` >>$2/upgrade.log
   heat stack-list >>$2/upgrade.log
   
   
fi

echo "Scaling Deployment Finished" >> $2/upgrade.log

exit 0

