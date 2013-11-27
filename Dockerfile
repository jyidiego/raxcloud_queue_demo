# DOCKER-VERSION 0.5.3
FROM ubuntu:12.10
MAINTAINER John Yi "john.yi@rackspace.com"

RUN apt-get -y update
RUN apt-get -y install curl build-essential libxml2-dev libxslt-dev git zlib1g-dev libssl-dev python openssh-server python-dev software-properties-common
RUN curl https://pypi.python.org/packages/source/s/setuptools/setuptools-1.1.6.tar.gz | (cd /root;tar xvzf -;cd setuptools-1.1.6;python setup.py install)
RUN easy_install pip
RUN pip install python-novaclient python-swiftclient python-heatclient python-cinderclient python-keystoneclient pyrax ansible python-glanceclient python-troveclient python-neutronclient supernova
# Setting the $HOME variable here
ENV HOME /root
# Uses raxcloud queues
# run consumer with: docker run -d raxcloud/raxcloud-queue-demo /usr/bin/python /root/consumer.py -u <username> -k <apikey> 
# run producer with: docker run -d raxcloud/raxcloud-queue-demo /usr/bin/python /root/producer.py -u <username> -k <apikey> 
ADD ./queue_demo.py $HOME/
ENTRYPOINT [ "/root/queue_demo.py" ]
