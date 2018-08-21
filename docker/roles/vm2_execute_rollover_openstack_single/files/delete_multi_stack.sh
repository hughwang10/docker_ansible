#!/bin/bash
#
# The script used to delete multi stacks for all ha groups via MIIT
#
# $1, new_dir: "{{ output_folder_remote }}/heat"
# $2, stack_name: "{{ os_stackname }}"

for hagroup in `ls -F $1/temp/ | grep "/" | sed 's/.$//'`
do

   echo "hagroup $hagroup"

   heat stack-delete $2_$hagroup

   sleep 30

   while [[ `heat stack-list | grep -w $2_$hagroup` != "" ]]; do
      heat stack-list 
      nova list 
      cinder list 
      sleep 10
   done

   echo "hagroup $hagroup has been deleted"
   # sleep 60
   # goto next hagroup

done

exit 0

