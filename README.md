raxcloud_queue_demo
===================

A simple demo of the rackspace cloud queues. This demo uses docker to setup the environment. You just need to run:

producer:

    docker run -d raxcloud/raxcloud-queue-demo /usr/bin/python <home directory>/producer.py -u <username> -k <apikey>


client:

    docker run -d raxcloud/raxcloud-queue-demo /usr/bin/python <home directory>/client.py -u <username> -k <apikey>


Here <username> and <apikey> are available in the mycloud.rackspace.com accounts link. The producer just posts a message at a fixed rate of time. The client claims and deletes a message at a fixed rate of time. You can run get_stats.py to see what the queue status is. This assumes that you use the same queue name for all of these scripts. For a full list of available options just run the producer.py or client.py without any options.

Usage: client.py [options]
Options:
  -h, --help            show this help message and exit
  -u USER, --user=USER  username
  -k API_KEY, --api_key=API_KEY
  -d                    
  -q QUEUE_NAME, --queue_name=QUEUE_NAME
                        queue name for cloud queue.
  -t TIME_INTERVAL, --time_interval=TIME_INTERVAL
                        time in seconds between message claim and deletion.
  -r REGION_NAME, --region_name=REGION_NAME
                        region (IAD, DFW, or ORD) for cloud queue.
You need -u or --user option

Usage: producer.py [options]
Options:
  -h, --help            show this help message and exit
  -u USER, --user=USER  username
  -k API_KEY, --api_key=API_KEY
                        apikey as shown in mycloud control panel.
  -d                    
  -q QUEUE_NAME, --queue_name=QUEUE_NAME
                        queue name for cloud queue.
  -t TIME_INTERVAL, --time_interval=TIME_INTERVAL
                        time in seconds between message posts to queue.
  -r REGION_NAME, --region_name=REGION_NAME
                        region (IAD, DFW, or ORD) for cloud queue.
You need -u or --user option

 
