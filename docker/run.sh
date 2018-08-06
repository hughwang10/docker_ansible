#!/bin/bash
docker run -it \
-v `pwd`:/project \
--rm --name afg-tools \
--network host \
hugh/ansible_docker