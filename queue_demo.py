#!/usr/bin/python

from optparse import OptionParser
from pprint import pprint
import pyrax
import random
import socket
import string
import sys
import time
import uuid

#
# Install file for docker
#
docker_install = '''#!/bin/bash

apt-get update
apt-get -y install linux-image-extra-`uname -r`

sh -c "wget -qO- https://get.docker.io/gpg | apt-key add -"
sh -c "echo deb http://get.docker.io/ubuntu docker main > /etc/apt/sources.list.d/docker.list"
apt-get update
apt-get -y install lxc-docker
'''
# pass files to pyrax(nova client) to create this file on the server
files = {"/tmp/docker_install.sh": docker_install}

def password_generator():
    characters = string.ascii_letters + '@!_#$&' + string.digits
    return "".join(random.choice(characters) for x in range(random.randint(8, 15)))


class Provisioner(object):
    def __init__(self):
        raise NotImplementedError

    def run(self):
        raise NotImplementedError


class ShellProvisioner(Provisioner):

    ''' Runs scripts and cmds to setup application on a server. Term stole from Vagrant's
        provisioner for application and configuration of a server.
    '''

    def __init__(self, cmds, client=None):

        ''' client: paramiko client that is already authenticated with server
            cmds: array of commands to run
        '''
        self.client = client
        self.cmds = cmds

    def set_client(self, client):
        self.client = client

    def run(self):
        print "Installing docker"
        stdin, stdout, stderr = self.client.exec_command(cmds[0])

        # print out stdout of the command execution
        for line in stdout:
            print '... ' + line.strip('\n')

        # run docker container 5 times
        for docker_instance in range(0, 5):
            stdin, stdout, stderr = client.exec_command(cmds[1])

            # print out stdout of the command execution
            for line in stdout:
                print '... ' + line.strip('\n')


class RaxCloudQueueClient(object):

    def __init__(self,
                 username,
                 api_key,
                 queue_name='demo0000',
                 time_interval=2,
                 region="IAD",
                 debug=False):

        pyrax.set_setting('identity_type', 'rackspace')
        if debug:
            print "username: %s" % username
            print "api_key: %s" % api_key
        pyrax.set_credentials(username, api_key)
        self.cq = pyrax.connect_to_queues(region=region)  # Demo to run out of IAD
        self.cq.client_id = str(uuid.uuid4())  # Randomly create a uuid client id
        if not self.cq.queue_exists(queue_name):
            self.cq.create(queue_name)
        self.queue_name = queue_name
        self.region = region
        self.time_interval = time_interval


class Producer(RaxCloudQueueClient):

    def run(self):
        i = 0
        while True:
            time.sleep(int(self.time_interval))
            try:
                print "message: %s" % \
                    self.cq.post_message(self.queue_name, "client-id: %s\nsequence: %d" % (self.cq.client_id, i), ttl=300)
            except pyrax.exceptions.ClientException, e:
                print "Couldn't post message: %s" % e
            except pyrax.exceptions.AuthenticationFailed, e:
                print "Authentication failed, will attempt to re-authenticate"

                # save the id to re-use
                client_id = self.cq.client_id

                region = self.cq.region_name
                self.cq = pyrax.connect_to_queues(region=region)
                self.cq.client_id = client_id
            i += 1


class Consumer(RaxCloudQueueClient):

    def run(self):
        while True:
            try:
                # take default 300 ttl and grace, 1 message per iter
                m = self.cq.claim_messages(self.queue_name, 300, 300, 1)
                if m:
                    print "Processing message id %s" % m.id
                    time.sleep(int(self.time_interval))
                    for i in m.messages:
                        i.delete(claim_id=i.claim_id)
                else:
                    print "No messages to process..."
                    time.sleep(5)
            except pyrax.exceptions.ClientException, e:
                print "Couldn't claim or delete message: %s" % e


class Status(RaxCloudQueueClient):

    def run(self):
        while True:
            pprint(self.cq.get_stats(self.queue_name))
            print
            time.sleep(int(self.time_interval))


class Monitor(object):

    def __init__(self,
                 rax_cld_queue_client,
                 scaling_group,
                 scale_up_threshold=100,
                 scale_dn_threshold=0,
                 time_interval=1):
        self.scale_group = scaling_group
        self.rax_queue = rax_cld_queue_client
        self.scale_up_threshold = scale_up_threshold
        self.scale_dn_threshold = scale_dn_threshold
        self.time_interval = time_interval

    def run(self):
        while True:
            pprint(self.rax_queue.cq.get_stats(self.rax_queue.queue_name))
            try:
                if self.rax_queue.cq.get_stats(self.rax_queue.queue_name)['free'] > int(self.scale_up_threshold):
                    self.scale_group.policy_up.execute()
                    print "Scaling up using policy %s" % self.scale_group.policy_up
                elif self.rax_queue.cq.get_stats(self.rax_queue.queue_name)['free'] <= int(self.scale_dn_threshold) and \
                        self.scale_group.sg.get_state()['active_capacity'] != 0:
                    self.scale_group.policy_dn.execute()
                    print "Scaling down using policy %s" % self.scale_group.policy_dn
            except pyrax.exceptions.Forbidden, e:
                print "Forbidden next time interval: %s" % e
                print "Wait for %d seconds for next retry" % (int(self.time_interval) + 20,)
                time.sleep(int(self.time_interval) + 20)
            except pyrax.exceptions.BadRequest, e:
                print "BadRequest next time interval: %s" % e
            except pyrax.exceptions.ClientException, e:
                print "ClientException next time interval: %s" % e
            time.sleep(int(self.time_interval))


class DemoScalingGroup(object):

    def __init__(self,
                 username,
                 api_key,
                 region,
                 group_name,
                 server_name='consumer',
                 cooldown=None,
                 min_entities=None,
                 max_entities=None,
                 flavor='performance1-1',
                 image=None,
                 load_balancers=(),
                 networks=[{'uuid': '11111111-1111-1111-1111-111111111111'},
                            {'uuid': '00000000-0000-0000-0000-000000000000'}],
                 metadata={},
                 debug=False):

        # set the scaling group attributes
        pyrax.set_setting('identity_type', 'rackspace')
        if debug:
            print "username: %s" % username
            print "api_key: %s" % api_key
            print "min_entites beg: %s" % min_entities
            print "max_entites beg: %s" % max_entities
        pyrax.set_credentials(username, api_key)
        self.sg = None
        self.au = pyrax.connect_to_autoscale(region=region)
        self.cq = pyrax.connect_to_queues(region=region)
        self.cs = pyrax.connect_to_cloudservers(region=region)
        self.server_name = server_name
        self.load_balancers = load_balancers
        self.networks = networks
        self.image = image
        self.flavor = flavor
        self.debug = debug

        if not group_name in [i.name for i in self.au.list()]:
            # set sane default values here scaling group creation
            self.cooldown = int(cooldown) or 60  # set default 60
            self.min_entities = int(min_entities) or 0  # set default to 0
            self.max_entities = int(max_entities) or 1  # set default to 1
            self._create_scaling_group(group_name, metadata)
        else:
            # go ahead and take default here however if they are empty they will
            # be overriden by an existing scaling group
            self.cooldown = int(cooldown)
            self.min_entities = int(min_entities)
            self.max_entities = int(max_entities)
            self._get_scaling_group(group_name, metadata)

    def _create_scaling_group(self, group_name, metadata):
        '''
        This will create a scaling group with default values.
        '''
        # load_balancers = ()
        self.sg = self.au.create(name=group_name,
                                 cooldown=self.cooldown,
                                 min_entities=self.min_entities,
                                 max_entities=self.max_entities,
                                 server_name=self.server_name,
                                 flavor=self.flavor,
                                 image=self.image,
                                 load_balancers=self.load_balancers,
                                 networks=self.networks,
                                 launch_config_type="launch_server",
                                 disk_config="AUTO")
        self.sg.update(metadata=metadata)

        self.policy_up = self.sg.add_policy(name="policy up",
                                            policy_type="webhook",
                                            cooldown=self.cooldown,
                                            change=1)

        self.policy_dn = self.sg.add_policy(name="policy down",
                                            policy_type="webhook",
                                            cooldown=self.cooldown,
                                            change=-1)

    def _get_scaling_group(self, group_name, metadata):
        sg_dict = dict([(sg.name, sg) for sg in self.au.list()])
        if group_name in sg_dict:
            self.sg = sg_dict[sg.name]
            sg_configs = self.sg.get_configuration()
            cooldown = self.cooldown or sg_configs['cooldown']
            min_entities = self.min_entities or sg_configs['minEntities']
            max_entities = self.max_entities or sg_configs['maxEntities']
            if metadata:
                self.sg.update(cooldown=cooldown,
                               min_entities=min_entities,
                               max_entities=max_entities,
                               metadata=metadata)
            else:
                self.sg.update(cooldown=cooldown,
                               min_entities=min_entities,
                               max_entities=max_entities)
                
            self.sg.reload()
            # update cooldown for policies, keep scaling group and policies with same cooldown
            for p in self.sg.list_policies():
                p.update(cooldown=cooldown)
                p.reload()

                # just expecting two policies one up one down
                if p.change == 1:
                    self.policy_up = p.reload()
                elif p.change == -1:
                    self.policy_dn = p.reload()

    def delete_scaling_group(self):
        if self.sg:
            self.sg.update(cooldown=0, min_entities=0, max_entities=0)
            self.sg.reload()
            self.policy_dn.update(cooldown=1)
            while self.sg.get_state()['active_capacity'] != 0:
                self.policy_dn.execute()
                time.sleep(2)
                self.sg.reload()
            snapshot_id = self.sg.metadata['snapshot_id']
            cs = self.cs.images.get(snapshot_id)
            cs.delete()
            queue_id = self.sg.metadata['queue_id']
            cq = self.cq.get(queue_id)
            cq.delete()
            self.sg.delete()


class ServerImage(object):

    def __init__(self,
                 username,
                 api_key,
                 region,
                 debug=False):

        pyrax.set_setting('identity_type', 'rackspace')
        self.debug = debug
        if self.debug:
            print "username: %s" % username
            print "api_key: %s" % api_key
        pyrax.set_credentials(username, api_key)
        self.cs = pyrax.connect_to_cloudservers(region=region)
        self.utils = pyrax.utils
        self.username = username
        self.api_key = api_key
        self.region = region

    def get_server_image(self, image_name):
        image_dict = dict([(i.name, i) for i in self.cs.list_images()])
        if image_name in image_dict:
            return image_dict[image_name]
        else:
            return None

    def create_server_image(self,
                            files,
                            snapshot_image_name='consumer-demo-template',
                            base_image_name='Ubuntu 13.10 (Saucy Salamander)',
                            flavor='performance1-1',
                            time_interval=1,
                            provisioner)

        ''' Build server, install docker, pull docker image, and delete server
        '''

        import paramiko
        image = self.get_server_image(base_image_name)
        if image:
            srv = self.cs.servers.create(snapshot_image_name, image.id, flavor, files=files)
        else:
            print "Couldn't find specified base image. Aborting."
            sys.exit(1)
        print "Creating server..."
        self.utils.wait_for_build(srv)
        password = password_generator()
        srv.change_password(password)
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        print "Password change taking effect..."
        time.sleep(5)  # give nova time to change the password
        if self.debug:
            print "srv.networks: %s" % srv.networks
            print "srv.networks['private'][0]: %s" % srv.networks['private'][0]

        try:
            client.connect(srv.networks['private'][0], username='root', password=password)
        except socket.error, e:
            print "hostname: %s" % srv.networks['private'][0]
            print "Attempted ssh connection on servicenet but failed."
            print "Couldn't ssh to the template server to run the installation. Are you in the right region?"
            print "Here's the stack trace and exception: %s" % e
            sys.exit(1)

        provisioner.set_client(client)
        provisioner.run()

        image_id = srv.create_image(snapshot_image_name)
        image = self.cs.images.get(image_id)
        print "Creating a snapshot of the image..."
        self.utils.wait_until(image, "status", ["ACTIVE", "ERROR"], attempts=0)
        srv.delete()
        return image


def main():

    #
    # Create may of class objects
    #

    mode0 = {"producer": Producer,
             "consumer": Consumer,
             "status": Status}

    mode1 = {"monitor": Monitor,
             "delete": Monitor}

    usage = '''Usage: queue_demo.py [options]

status: print out the queue status
consumer: claim and delete a message of the queue as specified by the options
producer: add a message onto the queue as specified by the options
monitor: use autoscale to spin up or down a server as specified by the options
delete: remove autoscale group by name. currently you have to delete queues
        manually. (if a server was provisioned by the scaling group that will
        be removed by this action.)

'''
    parser = OptionParser(usage=usage)
    parser.add_option("-u", "--user", dest="user", help="username")
    parser.add_option("-k", "--api_key", dest="api_key", help="apikey as shown in mycloud control panel.")
    parser.add_option("-d", action="store_true", help="debug", dest="debug")
    parser.add_option("-g", "--group_name", dest="group_name", help="scaling group name. default name demo", default="demo")
    parser.add_option("-c", "--cool_down", dest="cool_down", help="cool down time in seconds. default 60 secs.", default="60")
    parser.add_option("-x", "--max", dest="max", help="max number of servers in group. default 2.", default="2")
    parser.add_option("-m", "--min", dest="min", help="min number of servers in group. default 0.", default="0")
    parser.add_option("-i", "--image", dest="image", help="server image id.")
    parser.add_option("-l", "--flavor", dest="flavor", help="flavor name. default performance1-1", default="performance1-1")
    parser.add_option("-s", "--server_name", dest="server_name",
                      help="server name. default server name consumer.",
                      default="consumer")
    parser.add_option("-q", "--queue_name", dest="queue_name",
                      help="queue name for cloud queue. default is demo0000", default="demo0000")
    parser.add_option("-t", "--time_interval", dest="time_interval",
                      help="producer: time in seconds between message post to queue. \
 consumer: time in seconds between subscribing to a message and deleting. \
 monitor: time in seconds between queue monitoring. \
 status: time in seconds between status checks of the queue.",
                      default=2)
    parser.add_option("-r", "--region_name", dest="region_name",
                      help="region (IAD, DFW, or ORD) for cloud queue.",
                      default="IAD")
    parser.add_option("-j", "--scale_up_threshold", dest="scale_up_threshold",
                      help="Number of free messages (i.e. not claimed) to trigger scale up", default="100")
    parser.add_option("-n", "--scale_dn_threshold", dest="scale_dn_threshold",
                      help="Number of messages (i.e. not claimed) to trigger scale down", default="0")

    (options, args) = parser.parse_args()

    if not args:
        l = mode0.keys() + mode1.keys()
        print "You need to specify a mode like %s" % l
        sys.exit(1)

    if not options.user:
        parser.print_help()
        print "You need -u or --user option"
        sys.exit(1)

    if not options.api_key:
        parser.print_help()
        print "You need -a or --api_key option"
        sys.exit(1)

    if args[0] in mode0:
        obj_init = mode0[args[0]]
        m = obj_init(options.user,
                     options.api_key,
                     options.queue_name,
                     options.time_interval,
                     options.region_name,
                     options.debug)
    elif args[0] in mode1:
        if args[0] == 'delete':
            pyrax.set_setting('identity_type', 'rackspace')
            pyrax.set_credentials(options.user, options.api_key)
            au = pyrax.connect_to_autoscale(region=options.region_name)

            if options.group_name in [i.name for i in au.list()]:
                scaling_group = DemoScalingGroup(username=options.user,
                                                 api_key=options.api_key,
                                                 region=options.region_name,
                                                 group_name=options.group_name,
                                                 server_name=options.server_name,
                                                 cooldown=0,
                                                 min_entities=0,
                                                 max_entities=0,
                                                 flavor=options.flavor,
                                                 image=None,
                                                 debug=False)

                print "Delete scaling_group: %s (if not given --group_name option default is demo)" % scaling_group.sg.name
                scaling_group.delete_scaling_group()
                sys.exit(0)
            else:
                print "Scaling group %s doesn't exist (if not given --group_name option default is demo)" % options.group_name
                sys.exit(0)

        rax_cld_queue_client = RaxCloudQueueClient(options.user,
                                                   options.api_key,
                                                   options.queue_name,
                                                   options.time_interval,
                                                   options.region_name,
                                                   options.debug)

        # if options.image not set then try and create a image
        if not options.image:
            image_obj = ServerImage(username=options.user,
                                     api_key=options.api_key,
                                     region=options.region_name,
                                     debug=options.debug)

            # Retrieve existing snapshot named with snapshot_image_name
            image = image_obj.get_server_image(image_name='consumer-demo-template')

            if not image:
                # we installed the /tmp/docker_install.sh file with the arg files, installing it here
                install_docker = '/bin/bash /tmp/docker_install.sh'
                start_containers = \
                    "/usr/bin/docker run -d raxcloud/queue-demo consumer -u %s -k %s --region_name %s --time_interval %s" \
                                                      % (options.username, options.api_key,
                                                         options.region_name, options.time_interval)
                shell_provisioner = ShellProvisioner( [ install_docker, start_containers ] )
                image = image_obj.create_server_image(files=files,
                                                      snapshot_image_name='consumer-demo-template',
                                                      base_image_name='Ubuntu 13.10 (Saucy Salamander)',
                                                      flavor=options.flavor,
                                                      time_interval=options.time_interval,
                                                      provisioner=shell_provisioner)
                if not image:
                    parser.print_help()
                    print "You need -i or --image option"
                    sys.exit(1)
        else:
            pyrax.set_setting('identity_type', 'rackspace')
            cs = pyrax.connect_to_cloudservers(region=options.region_name)
            # Really just need image id but may need
            # image object sometime in the future
            image = cs.images.get(options.image)

        metadata = {'queue_id' : rax_cld_queue_client.queue_name,
                    'snapshot_id' : image.id}

        scaling_group = DemoScalingGroup(username=options.user,
                                         api_key=options.api_key,
                                         region=options.region_name,
                                         group_name=options.group_name,
                                         server_name=options.server_name,
                                         cooldown=options.cool_down,
                                         min_entities=options.min,
                                         max_entities=options.max,
                                         flavor=options.flavor,
                                         image=image.id,
                                         metadata=metadata,
                                         debug=False)

        m = Monitor(rax_cld_queue_client=rax_cld_queue_client,
                    scaling_group=scaling_group,
                    scale_up_threshold=options.scale_up_threshold,
                    scale_dn_threshold=options.scale_dn_threshold,
                    time_interval=options.time_interval)

    else:
        print "The mode %s doesn't exist it must be one of %s" \
            % (args[0], mode0.keys() + mode1.keys())
        sys.exit(1)

    try:
        m.run()
    except KeyboardInterrupt:
        print "Bye!"

if __name__ == "__main__":
    main()
