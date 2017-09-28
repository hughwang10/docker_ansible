#!/bin/bash
# example
docker run -it \
  -v /media/sf_myshare/projects/vf_Ireland_2017/SA_680AFGT/out_result/site_spec:/opt/miep/tools/miit/msp_miit/site-config/tmp/site_spec \
  -v /media/sf_myshare/projects/vf_Ireland_2017/SA_680AFGT/out_result/vars:/opt/miep/tools/miit/msp_miit/site-config/tmp/vars \
  -v /media/sf_myshare/projects/vf_Ireland_2017/SA_680AFGT/out_result:/opt/miep/tools/miit/msp_miit/site-config/result \
  -v /media/sf_myshare/projects/vf_Ireland_2017/archive:/opt/miep/tools/miit/system-images/archive \
  -v /media/sf_myshare/projects/vf_Ireland_2017/SA_680AFGT/miit_cmd.sh:/opt/miep/tools/miit/msp_miit/site-config/tmp/miit_cmd.sh \
  -v /media/sf_myshare/projects/vf_Ireland_2017/SA_680AFGT/test.yml:/opt/miep/tools/miit/msp_miit/site-config/test.yml \
  --rm --name 680AFGT \
  --network host  \
  hugh/toolsvm_ansible:1.9 \
  /bin/bash
