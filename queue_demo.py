#!/usr/bin/python

from optparse import OptionParser
from pprint import pprint
import pyrax
import sys
import time
import uuid


class RaxCloudQueueClient(object):

    def __init__(self, username, api_key, queue_name='demo0000', time_interval=2, region="IAD", debug=False ):
        pyrax.set_setting('identity_type', 'rackspace')
        if debug:
            print "username: %s" % username
            print "api_key: %s" % api_key
        pyrax.set_credentials( username, api_key )
        self.cq = pyrax.connect_to_queues(region=region) # Demo to run out of IAD
        self.cq.client_id = str(uuid.uuid4()) # Randomly create a uuid client id
        self.queue_name = queue_name
        self.time_interval = time_interval

class Producer(RaxCloudQueueClient):

    def __init__(self, *args, **kwargs): 
        super(Producer, self).__init__(*args, **kwargs)
        #
        # Create cloud queue if this does not exist.
        #
        if not self.cq.queue_exists( self.queue_name ):
            self.cq.create( self.queue_name )

    def run(self):
        i = 0
        while True:
            time.sleep( int(self.time_interval))
            try:
                print "message: %s" % \
                    self.cq.post_message(self.queue_name, "client-id: %s\nsequence: %d" % (self.cq.client_id, i), ttl=300)
            except pyrax.exceptions.ClientException,e:
                print "Couldn't post message: %s" % e
            i += 1

class Consumer(RaxCloudQueueClient):

    def run( self ):
        while True:
            try:
                m = self.cq.claim_messages(self.queue_name, 300, 300, 1) # take default 300 ttl and grace, 1 message per iter
                if m:
                    print "Processing message id %s" % m.id
                    time.sleep( int(self.time_interval) )
                    for i in m.messages:
                        i.delete(claim_id=i.claim_id)
                else:
                    print "No messages to process..."
            except pyrax.exceptions.ClientException,e:
                print "Couldn't claim or delete message: %s" % e


class Status(RaxCloudQueueClient):
    
    def run(self):
        while True:
            pprint(self.cq.get_stats(self.queue_name))
            print
            time.sleep( int(self.time_interval) )

class Monitor(RaxCloudQueueClient):

    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        print "args: %s" % args[4]
        self.au = pyrax.connect_to_autoscale(region=args[4])
        self.sg = None
        self.policy_up = self.policy_dn = None

    def create_scaling_group(self, group_name, \
                             min_entities, max_entities, server_name, \
                             cooldown, flavor, image, scale_up_threshold, scale_dn_threshold, \
                             load_balancers=(), \
                             networks=[ {'uuid': '11111111-1111-1111-1111-111111111111'}, \
                                        {'uuid': '00000000-0000-0000-0000-000000000000'} ] ):
        '''
        This will create a a scaling group with default values.
        '''
        # metadata = {}
        # load_balancers = ()
        self.scale_up_threshold = scale_up_threshold
        self.scale_dn_threshold = scale_dn_threshold
        self.sg = self.au.create( name=group_name, cooldown=cooldown, min_entities=min_entities, \
                                  max_entities=max_entities, server_name=server_name, \
                                  flavor=flavor, image=image, load_balancers=load_balancers, networks=networks, \
                                  launch_config_type="launch_server", disk_config="AUTO" )
        self.policy_up = self.sg.add_policy( name="policy up", policy_type="webhook", \
                                          cooldown=cooldown, change=1 )
        self.policy_dn = self.sg.add_policy( name="policy down", policy_type="webhook", \
                                          cooldown=cooldown, change=-1 )

    def get_scaling_group(self, group_name, scale_up_threshold, scale_dn_threshold):
        for sg in self.au.list():
            if group_name == sg.name:
                self.sg = sg
                self.scale_up_threshold = scale_up_threshold
                self.scale_dn_threshold = scale_dn_threshold
                # this is horrible but expect just one up policy and one down.
                for i in sg.policies:
                    if i.change == 1:
                       self.policy_up = i
                    elif i.change == -1:
                       self.policy_dn = i

    def delete_scaling_group(self):
        if self.sg:
            self.sg.delete()

    def list_policies(self):
        return self.sg.list_policies()
    
    def run(self):
        while True:
            pprint(self.cq.get_stats(self.queue_name))
            try:
                if self.cq.get_stats(self.queue_name)['free'] > int(self.scale_up_threshold):
                    self.policy_up.execute()
                    print "Scaling up using policy %s" % self.policy_up 
                elif self.cq.get_stats(self.queue_name)['free'] < int(self.scale_dn_threshold) and \
                        self.sg.get_state()['active_capacity'] != 0:
                    self.policy_dn.execute()
                    print "Scaling down using policy %s" % self.policy_dn
            except pyrax.exceptions.Forbidden,e:
                print "Policy didn't execute waiting for next time interval: %s" % e
            time.sleep( int(self.time_interval) )


def main():
    #
    # Create may of class objects
    #
    mode0 = { "producer" : Producer,
              "consumer" : Consumer,
              "status"   : Status } 
    mode1 = { "monitor"  : Monitor }
    parser = OptionParser()
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
                      help="queue name for cloud queue.", default="demo0000")
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
        m = obj_init(options.user, options.api_key, options.queue_name, options.time_interval, options.region_name, options.debug)
    elif args[0] in mode1: 
        obj_init = mode1[args[0]]
        m = obj_init(options.user, options.api_key, options.queue_name, options.time_interval, options.region_name, options.debug)
        if not options.image:
            parser.print_help()
            print "You need -i or --image option"
            sys.exit(1)
        if not options.group_name in [ i.name for i in m.au.list() ]:
            m.create_scaling_group( options.group_name, int(options.min), int(options.max), \
                                    options.server_name, int(options.cool_down), options.flavor, \
                                    options.image, options.scale_up_threshold, options.scale_dn_threshold )
        else:
            m.get_scaling_group(options.group_name, options.scale_up_threshold, options.scale_dn_threshold)
            print "Scaling group already exists."

    else:
        print "The mode %s doesn't exist it must be one of %s" % (args[0], mode0.keys() + mode1.keys())
        sys.exit(1)

    try:
        m.run()
    except KeyboardInterrupt:
       print "Bye!"

if __name__ == "__main__":
    main()
