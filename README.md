raxcloud_queue_demo
===================

A simple demo of the rackspace cloud queues. This demo uses docker to setup the environment. You just need to run:

producer:

    docker run -d raxcloud/raxcloud-queue-demo producer -u <username> -k <apikey>


consumer:

    docker run -d raxcloud/raxcloud-queue-demo consumer -u <username> -k <apikey>


Here <username> and <apikey> are available in the mycloud.rackspace.com accounts link. The producer just posts a message at a fixed rate of time. The consumer claims and deletes a message at a fixed rate of time. You can run get_stats.py to see what the queue status is. This assumes that you use the same queue name for all of these scripts. For a full list of available options just run the queue_demo.py without any options.

```
You need to specify a mode like ['status', 'consumer', 'producer']
Usage: queue_demo.py [options]

Options:
  -h, --help            show this help message and exit
  -u USER, --user=USER  username
  -k API_KEY, --api_key=API_KEY
                        apikey as shown in mycloud control panel.
  -d                    debug
  -q QUEUE_NAME, --queue_name=QUEUE_NAME
                        queue name for cloud queue.
  -t TIME_INTERVAL, --time_interval=TIME_INTERVAL
                        producer: time in seconds between message post to
                        queue.                              consumer: time in
                        seconds between subscribing to a message and deleting.
                        status: time in seconds between status checks of the
                        queue.
  -r REGION_NAME, --region_name=REGION_NAME
                        region (IAD, DFW, or ORD) for cloud queue.
```
