Rackspace Cloud Queue Demo
===================

A simple demo of the rackspace cloud queues. This particular demo shows a simple work queue (Producer/Consumer or transactional job queue). To setup this demo do the following:

Installing Docker
-----------------
```
You'll need to provision a server with docker installed on it. The following
instructions will provision a Rackspace cloudserver.
1. Setup the environment variables for the nova client:
OS_REGION_NAME=IAD
OS_TENANT_ID= 
OS_PASSWORD=<password>
OS_AUTH_URL=https://identity.api.rackspacecloud.com/v2.0
OS_USERNAME=<username>
where username and password is the Rackspace username and password you use to log
into the cloud control panel. OS_TENANT_ID just needs to be defined but leave
that blank as above

2. Get the Ubuntu 13.10 image id by running the following:
IMG_ID=$(nova image-list | grep 'Ubuntu 13.10' | cut -d'|' -f2)

3. Once you have an IMG_ID environment variable run nova to provision a server:
nova boot --flavor performance1-1 --image $IMG_ID --poll queue.demo

You should see something similiar to this:
+------------------------+--------------------------------------+
| Property               | Value                                |
+------------------------+--------------------------------------+
| status                 | BUILD                                |
| updated                | 2014-01-02T18:40:21Z                 |
| OS-EXT-STS:task_state  | scheduling                           |
| key_name               | None                                 |
| image                  | Ubuntu 13.10 (Saucy Salamander)      |
| hostId                 |                                      |
| OS-EXT-STS:vm_state    | building                             |
| flavor                 | 1 GB Performance                     |
| id                     | c423a604-a3f5-462e-ace3-dac1bfc30828 |
| user_id                | 10044828                             |
| name                   | queue.demo                           |
| adminPass              | JLy7gUXudx9c                         |
| tenant_id              | 843368                               |
| created                | 2014-01-02T18:40:21Z                 |
| OS-DCF:diskConfig      | AUTO                                 |
| accessIPv4             |                                      |
| accessIPv6             |                                      |
| progress               | 0                                    |
| OS-EXT-STS:power_state | 0                                    |
| config_drive           |                                      |
| metadata               | {}                                   |
+------------------------+--------------------------------------+
Instance building... 100% complete
Finished

4. ssh into your completed server, you can use nova to do this by running:
nova ssh queue.demo

You'll see something similiar to this:
The authenticity of host '162.242.214.102 (162.242.214.102)' can't be established.
ECDSA key fingerprint is 2a:10:1f:9a:2b:92:82:d9:00:00:c4:53:3b:54:9b:57.
Are you sure you want to continue connecting (yes/no)? yes
Warning: Permanently added '162.242.214.102' (ECDSA) to the list of known hosts.
root@162.242.214.102's password: 

The programs included with the Ubuntu system are free software;
the exact distribution terms for each program are described in the
individual files in /usr/share/doc/*/copyright.

Ubuntu comes with ABSOLUTELY NO WARRANTY, to the extent permitted by
applicable law.

root@queue:~# 


5. Once logged in install docker by running the following sequence of commands (you can copy and paste):
cat <<EOF > /tmp/docker_install.sh
apt-get update
apt-get -y install linux-image-extra-`uname -r`
sh -c "wget -qO- https://get.docker.io/gpg | apt-key add -"
sh -c "echo deb http://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list"
apt-get update
apt-get -y install lxc-docker
EOF

Then run:
root@queue:~# bash /tmp/docker_install.sh

6. Verify that docker was installed correctly by doing the following:
root@queue:~# docker run -i -t ubuntu:12.10 bash
Unable to find image 'ubuntu:12.10' (tag: 12.10) locally
Pulling repository ubuntu
b750fe79269d: Download complete 
27cf78414709: Download complete 

Type hostname to verify your in the container:
root@af2db68e3262:/# hostname
af2db68e3262

Exit the container:
root@af2db68e3262:/# exit
exit

Pull the queue-demo from the docker registry
root@queue:~# docker pull raxcloud/queue-demo

You should see:
Pulling repository raxcloud/queue-demo
babc815ad36f: Download complete 
27cf78414709: Download complete 
b750fe79269d: Download complete 
6acd24ff2183: Download complete 
3cc2dc19c052: Download complete 
0f44a23a4e43: Download complete 
de96c1029bfc: Download complete 
791d8ad51d49: Download complete 
3613148d5f3d: Download complete 
0afc74fad907: Download complete 
bee739d4bf76: Download complete 

```

Setting up the Demo
-------------------
```
1. First you need start the monitoring process for example:

docker run -d raxcloud/queue-demo monitor -u test000 -k fffffffeeeeeee \
--region_name IAD -x 1 -m 0 -j 100 -n 0

-x is maximum number of servers
-m is minimum number of servers
-j is upper threshold for free messages on the queue (scale up trigger)
-n is the lower threshold for messages on the queue (scale down trigger)

If this is the first time you've run the demo it may take a while as it does the following:
  1. create the autoscale scaling group (default name demo)
  2. create the cloud queue (default name demo0000)
  3. create a cloudserver
  4. install docker on the server
  5. run a container on docker service
  6. take a snapshot of the cloud server (consumer-demo-template)
  7. delete the cloud server

2. Once you've set up the monitoring process, you need to run the producer to get messages on the queue.

docker run -d raxcloud/queue-demo producer -u test000 -k fffffffeeeeeee --region_name IAD --time_interval 1  

--time_interval is the number of seconds between a single message being placed on the queue

```


Here `username` and `apikey` are available in the mycloud.rackspace.com accounts link. The producer just posts a message at a fixed rate of time. The consumer claims and deletes a message at a fixed rate of time. You can run status to see what the queue status is. This assumes that you use the same queue name for all of these scripts. For a full list of available options just run the queue_demo.py without any options.

```
You need to specify a mode like ['status', 'consumer', 'producer', 'monitor']
Usage: queue_demo.py [options]
status: print out the queue status
consumer: claim and delete a message of the queue as specified by the options
producer: add a message onto the queue as specified by the options
monitor: use autoscale to spin up or down a server as specified by the options
delete: remove autoscale group by name. currently you have to delete queues
        manually. (if a server was provisioned by the scaling group that will
        be removed by this action.)

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
