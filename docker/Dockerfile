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

RUN mkdir -p /etc/ansible/
RUN echo 'localhost ansible_connection=local' > /etc/ansible/hosts
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD library /etc/ansible/library
ADD roles /etc/ansible/roles

# CMD ansible-playbook --version
WORKDIR /project
ENTRYPOINT ["/project/entrypoint.sh"]