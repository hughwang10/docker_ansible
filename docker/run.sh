#!/bin/bash
# example
docker run -it \
-v `pwd`:/project \
--rm --name afg-toolsvm \
--network host  \
hugh/ansible_docker \
# /bin/bash
