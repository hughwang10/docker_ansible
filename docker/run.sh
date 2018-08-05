#!/bin/bash
# example
docker run -it \
  -v /home/hugh/myshare/projects/docker_ansible/:/tmp \
  --rm --name afg-toolsvm \
  --network host  \
  hugh/ansible_docker \
  /bin/bash
