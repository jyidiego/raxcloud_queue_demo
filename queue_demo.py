#!/usr/bin/python

from optparse import OptionParser
from pprint import pprint
import pyrax
import sys
import time
import uuid

#
# Create may of class objects
#
mode = { "producer" : Producer,
         "consumer" : Consumer,
         "status"   : Monitor }

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
            self.cq.create( queue_name )

    def run(self):
        i = 0
        while True:
            time.sleep( int(self.time_interval))
            print "message: %s" % \
                self.cq.post_message(self.queue_name, "client-id: %s\nsequence: %d" % (self.cq.client_id, i), ttl=300)
            i += 1

class Consumer(RaxCloudQueueClient):

    def run( self ):
        while True:
            m = self.cq.claim_messages(self.queue_name, 300, 300, 1) # take default 300 ttl and grace, 1 message per iter
            if m:
                print "Processing message id %s" % m.id
                time.sleep( int(self.time_interval) )
                for i in m.messages:
                    i.delete(claim_id=i.claim_id)
            else:
                print "No messages to process..."

class Monitor(RaxCloudQueueClient):
    
    def run(self):
        while True:
            pprint(self.cq.get_stats(self.queue_name))
            print
            time.sleep( int(self.time_interval) )


def main():
    parser = OptionParser()
    parser.add_option("-u", "--user", dest="user", help="username")
    parser.add_option("-k", "--api_key", dest="api_key", help="apikey as shown in mycloud control panel.")
    parser.add_option("-d", action="store_true", help="debug", dest="debug")
    parser.add_option("-q", "--queue_name", dest="queue_name",
                      help="queue name for cloud queue.", default="demo0000")
    parser.add_option("-t", "--time_interval", dest="time_interval",
                      help="producer: time in seconds between message post to queue.\n \
                            consumer: time in seconds between subscribing to a message and deleting.\n \
                            status: time in seconds between status checks of the queue.",
                      default=2)
    parser.add_option("-r", "--region_name", dest="region_name",
                      help="region (IAD, DFW, or ORD) for cloud queue.",
                      default="IAD")
    (options, args) = parser.parse_args()

    if not args:
        print "You need to specify a mode like %s" % mode.keys()
        sys.exit(1)

    if not options.user:
        parser.print_help()
        print "You need -u or --user option"
        sys.exit(1)
    if not options.api_key:
        parser.print_help()
        print "You need -a or --api_key option"
        sys.exit(1)

    if args[0] in mode: 
        obj_init = mode[args[0]]
        m = obj_init(options.user, options.api_key, options.queue_name, options.time_interval, options.region_name, options.debug)
    else:
        print "The mode %s doesn't exist it must be one of %s" % (args[0], mode.keys())
        sys.exit(1)

    try:
        m.run()
    except KeyboardInterrupt:
       print "Bye!"

if __name__ == "__main__":
    main()
