#!/bin/bash
docker build --network host -t hugh/toolsvm_ansible:1.9 .
docker rmi $(docker images -q --filter "dangling=true")
docker images
