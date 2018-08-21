FROM ubuntu:18.04
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get -y update && \
    apt-get -y --fix-missing install software-properties-common sshpass openssh-client python-pip python-selinux python-dev

RUN pip install --upgrade pip

#ansible
RUN pip install -U 'requests[security]' netaddr pyVmomi pysphere cryptography
RUN pip install ansible==1.9.6
RUN mkdir -p /etc/ansible/
RUN echo 'localhost ansible_connection=local' > /etc/ansible/hosts
ADD ansible.cfg /etc/ansible/ansible.cfg
ADD library /etc/ansible/library
ADD roles /etc/ansible/roles

# CMD ansible-playbook --version
WORKDIR /project
ENTRYPOINT ["/project/entrypoint.sh"]