FROM williamyeh/ansible:1.9-ubuntu14.04
MAINTAINER Hugh Wang
ENV DEBIAN_FRONTEND noninteractive
RUN \
	apt-get update && \
	apt-get -y upgrade && \
	apt-get autoremove && apt-get autoclean
RUN \
	apt-get -y install sshpass ansible sudo python-pip genisoimage tar && \
	pip install --upgrade pip
RUN \
	pip install 'requests[security]' netaddr pyVmomi pysphere
RUN \
	groupadd miepgrp && \
	useradd -m -g miepgrp miepadm
COPY toolsvm/site-config /opt/miep/tools/miit/msp_miit/site-config 
RUN chown -R miepadm:miepgrp /opt
RUN chmod -R 755 /opt

#USER miepadm
WORKDIR /opt/miep/tools/miit/msp_miit/site-config
ADD entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]