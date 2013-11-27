raxcloud_queue_demo
===================

A simple demo of the rackspace cloud queues. This demo uses docker to setup the environment. You just need to run:

producer:
    docker run -d raxcloud/raxcloud-queue-demo /usr/bin/python <home directory>/producer.py -u <username> -k <apikey>

client:
    docker run -d raxcloud/raxcloud-queue-demo /usr/bin/python <home directory>/client.py -u <username> -k <apikey>

The producer just posts a message at a fixed rate of time. The client claims and deletes a message at a fixed rate of time. 
