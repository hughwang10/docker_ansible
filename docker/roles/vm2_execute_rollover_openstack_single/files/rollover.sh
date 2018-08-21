#!/bin/bash

# $1,   source_dir: "{{ output_folder_remote }}/heat" 
# $2,   dest_dir: "{{ output_folder_remote }}/upgrade/2" 
# $3,   vms: "{{ vms_per_batch | default(2) }}" 
# $4,   template_file: "{{ os_msptemplate}}" 
# $5,   stack_name: "{{ os_stackname }}"

count=0

echo `date` >>$2/rollover.log
echo "Rollover for Bulk Upgrade Start" >> $2/rollover.log

for file in `ls -tr $1/temp`
do

   echo "copy $1/temp/$file to dir $2/temp/" >>$2/rollover.log

   cp $1/temp/$file $2/temp/
   
   vm_name=${file%.yaml}

   echo "delete $2/temp/$vm_name-vols.yaml" >>$2/rollover.log

   rm $2/temp/$vm_name-vols.yaml  

   let "count=$count+1"
 
   p=`expr $count % $3`        
  
   if [ "$p" = "0" ]; then
      
      cat $2/temp/*.yaml > $2/$4

      cat $2/$4 >>$2/rollover.log

      echo `date` >>$2/rollover.log
      echo "update the stack now" >>$2/rollover.log
 
      heat stack-update -f $2/$4 $5

      sleep 60

      while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_FAIL" ]]; do
         echo `date` >>$2/rollover.log
         heat stack-list >>$2/rollover.log
         nova list >>$2/rollover.log
         cinder list >>$2/rollover.log
         sleep 10 
      done

   echo `date` >>$2/rollover.log
   heat stack-list >>$2/rollover.log
      
 
   fi

done

p=`expr $count % $3`        
  
if [ "$p" != "0" ]; then
      
   cat $2/temp/*.yaml > $2/$4

   cat $2/$4 >>$2/rollover.log

   echo `date` >>$2/rollover.log
   echo "update the stack now" >>$2/rollover.log

   sleep 60

   heat stack-update -f $2/$4 $5

   sleep 60

   while [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_COMPLETE" ]] && [[ `heat stack-list | grep $5 | awk '{print $6}'` != "UPDATE_FAIL" ]]; do
      echo `date` >>$2/rollover.log
      heat stack-list >>$2/rollover.log
      nova list >>$2/rollover.log
      cinder list >>$2/rollover.log
      sleep 10 
   done

   echo `date` >>$2/rollover.log
   heat stack-list >>$2/rollover.log
   
   
fi

echo "Rollover for Bulk Upgrade Finished" >> $2/rollover.log

exit 0

