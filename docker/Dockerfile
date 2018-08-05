FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive

RUN \
    apt-get -y update && \
    apt-get -y install software-properties-common && \
    apt-add-repository ppa:ansible/ansible  && \
    apt-get -y update
RUN apt-get -y install ansible sshpass openssh-client python-pip python-selinux python-dev
RUN pip install --upgrade pip
RUN \
	pip install 'requests[security]' netaddr pyVmomi pysphere

RUN echo 'localhost ansible_connection=local' > /etc/ansible/hosts

# CMD ansible-playbook --version
WORKDIR /project
ENTRYPOINT ["/project/entrypoint.sh"]