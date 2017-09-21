FROM williamyeh/ansible:1.9-ubuntu14.04
MAINTAINER Hugh Wang
ENV DEBIAN_FRONTEND noninteractive
RUN \
	apt-get update && \
	apt-get -y upgrade && \
	apt-get autoremove && apt-get autoclean && \
	apt-get -y install sshpass ansible sudo python-pip genisoimage tar && \
	pip install --upgrade pip && \
	pip install 'requests[security]' netaddr pyVmomi pysphere && \
	groupadd miepgrp && \
	useradd -m -g miepgrp miepadm
RUN mkdir -p /opt/miep/tools/miit
COPY toolsvm/site-config /opt/miep/tools/miit/msp_miit/site-config 
RUN chown -R miepadm:miepgrp /opt
RUN chmod -R 755 /opt

#USER miepadm
WORKDIR /opt/miep/tools/miit/msp_miit/site-config
ADD entrypoint.sh /
ENTRYPOINT ["/entrypoint.sh"]