from optparse import OptionParser
import pyrax
import pprint
import sys
import time
import uuid

class Monitor(object):

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

    def run(self):
        while True:
            pprint.pprint("%s" % self.cq.get_stats(self.queue_name))
            print
            time.sleep( self.time_interval )

def main():
    parser = OptionParser()
    parser.add_option("-u", "--user", dest="user", help="username")
    parser.add_option("-k", "--api_key", dest="api_key", help="apikey as shown in mycloud control panel.")
    parser.add_option("-d", action="store_true", help="debug", dest="debug")
    parser.add_option("-q", "--queue_name", dest="queue_name",
                      help="queue name for cloud queue.", default="demo0000")
    parser.add_option("-t", "--time_interval", dest="time_interval",
                      help="time in seconds between status.",
                      default=5)
    parser.add_option("-r", "--region_name", dest="region_name",
                      help="region (IAD, DFW, or ORD) for cloud queue.",
                      default="IAD")
    (options, args) = parser.parse_args()
    if not options.user:
        parser.print_help()
        print "You need -u or --user option"
        sys.exit(1)
    if not options.api_key:
        parser.print_help()
        print "You need -a or --api_key option"
        sys.exit(1)

    p = Monitor(options.user, options.api_key, options.queue_name, int(options.time_interval), options.region_name, options.debug)
    try:
        p.run()
    except KeyboardInterrupt:
       print "Bye!"

if __name__ == "__main__":
    main()

