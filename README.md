Rackspace Cloud Queue Demo
===================

A simple demo of the rackspace cloud queues. This particular demo shows a simple work queue (Producer/Consumer or transactional job queue). To setup this demo run:

producer:

    docker run -d raxcloud/queue-demo producer -u <username> -k <apikey>


consumer:

    docker run -d raxcloud/queue-demo consumer -u <username> -k <apikey>


Here `username` and `apikey` are available in the mycloud.rackspace.com accounts link. The producer just posts a message at a fixed rate of time. The consumer claims and deletes a message at a fixed rate of time. You can run status to see what the queue status is. This assumes that you use the same queue name for all of these scripts. For a full list of available options just run the queue_demo.py without any options.

```
You need to specify a mode like ['status', 'consumer', 'producer']
Usage: queue_demo.py [options]

Options:
  -h, --help            show this help message and exit
  -u USER, --user=USER  username
  -k API_KEY, --api_key=API_KEY
                        apikey as shown in mycloud control panel.
  -d                    debug
  -g GROUP_NAME, --group_name=GROUP_NAME
                        scaling group name. default name demo
  -c COOL_DOWN, --cool_down=COOL_DOWN
                        cool down time in seconds. default 60 secs.
  -x MAX, --max=MAX     max number of servers in group. default 2.
  -m MIN, --min=MIN     min number of servers in group. default 0.
  -i IMAGE, --image=IMAGE
                        server image id.
  -l FLAVOR, --flavor=FLAVOR
                        flavor name. default performance1-1
  -s SERVER_NAME, --server_name=SERVER_NAME
                        server name. default server name consumer.
  -q QUEUE_NAME, --queue_name=QUEUE_NAME
                        queue name for cloud queue. default is demo0000
  -t TIME_INTERVAL, --time_interval=TIME_INTERVAL
                        producer: time in seconds between message post to
                        queue.  consumer: time in seconds between subscribing
                        to a message and deleting.  monitor: time in seconds
                        between queue monitoring.  status: time in seconds
                        between status checks of the queue.
  -r REGION_NAME, --region_name=REGION_NAME
                        region (IAD, DFW, or ORD) for cloud queue.
  -j SCALE_UP_THRESHOLD, --scale_up_threshold=SCALE_UP_THRESHOLD
                        Number of free messages (i.e. not claimed) to trigger
                        scale up
  -n SCALE_DN_THRESHOLD, --scale_dn_threshold=SCALE_DN_THRESHOLD
                        Number of messages (i.e. not claimed) to trigger scale
                        down
```
