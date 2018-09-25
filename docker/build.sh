#!/bin/bash
#--no-cache
docker build --no-cache --network host -t hugh/ansible_docker .
docker rmi $(docker images -q --filter "dangling=true")
docker images
