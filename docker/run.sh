#!/bin/bash
docker run -it \
  -v /home/hugh/myshare/projects/TIM_AFG/live_development/out_result/site_spec:/opt/miep/tools/miit/msp_miit/site-config/tmp/site_spec \
  -v /home/hugh/myshare/projects/TIM_AFG/live_development/out_result/vars:/opt/miep/tools/miit/msp_miit/site-config/tmp/vars \
  -v /home/hugh/result:/opt/miep/tools/miit/msp_miit/site-config/result \
  -v /home/hugh/myshare/projects/TIM_AFG/live_development/out_result/miit_cmd.sh:/opt/miep/tools/miit/msp_miit/site-config/tmp/miit_cmd.sh \
  --rm --name test \
  --network host  \
  hugh/toolsvm_ansible:1.9 \
  /bin/bash
