#!/usr/bin/python

from optparse import OptionParser
from pprint import pprint
import pyrax
import sys
import time
import uuid
import queue_demo


class Monitor(queue_demo.RaxCloudQueueClient):

    def __init__(self, *args, **kwargs):
        super(Monitor, self).__init__(*args, **kwargs)
        self.au = pyrax.connect_to_autoscale(region=kwargs['region'])
        self.sg = None
        self.policy_up = self.policy_dn = None

    def create_scaling_group(self, group_name, \
                             min_entities, max_entities, server_name, \
                             cooldown, flavor, image, free_count, load_balancers=(), \
                             networks=[ {'uuid': '11111111-1111-1111-1111-111111111111'}, \
                                        {'uuid': '00000000-0000-0000-0000-000000000000'} ] ):
        '''
        This will create a a scaling group with default values.
        '''
        # metadata = {}
        # load_balancers = ()
        self.sg = self.au.create( name=group_name, cooldown=cooldown, min_entities=min_entities, \
                           max_entities=max_entities, server_name=server_name, \
                           flavor=flavor, image=image, load_balancers=load_balancers, networks=networks, \
                           launch_config_type="launch_server", disk_config="AUTO" )
        self.policy_up = self.sg.add_policy( name="policy up", policy_type="webhook", \
                                          cooldown=cooldown, change=1 )
        self.policy_dn = self.sg.add_policy( name="policy down", policy_type="webhook", \
                                          cooldown=cooldown, change=-1 )
        pass

    def delete_scaling_group(self):
        if self.sg:
            self.sg.delete()

    def list_policies(self):
        return self.sg.list_policies()
    
    def run(self):
        while True:
            if self.cq.get_stats(self.queue_name)['free'] > int(free_count):
                self.policy_up.execute()
                print "Scaling up using policy %s" % self.policy 
            elif self.cq.get_stats(self.queue_name)['free'] < int(free_count) and \
                    self.sg.get_state()['active_capacity'] != 0:
                self.policy_dn.execute()
                print "Scaling down using policy %s" % self.policy 
            time.sleep( int(self.time_interval) )


def main():
    #
    # Create may of class objects
    #
    mode = { "status"   : Monitor }
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
                      help="status: time in seconds between status checks of the queue.",
                      default=2)
    parser.add_option("-r", "--region_name", dest="region_name",
                      help="region (IAD, DFW, or ORD) for cloud queue.",
                      default="IAD")
    parser.add_option("-f", "--free_count", dest="free_count",
                      help="Number of free messages (i.e. not claimed) to trigger autoscale", default="100")
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
    if not options.image:
        parser.print_help()
        print "You need -i or --image option"
        sys.exit(1)

    if args[0] in mode: 
        obj_init = mode[args[0]]
        m = obj_init(options.user, options.api_key, options.queue_name, options.time_interval, options.region_name, options.debug)
        m.create_scaling_group( options.group_name, int(options.cool_down), int(options.min), \
                                int(options.max), options.server_name, options.flavor, \
                                options.image, options.free_count)
    else:
        print "The mode %s doesn't exist it must be one of %s" % (args[0], mode.keys())
        sys.exit(1)

    try:
        m.run()
    except KeyboardInterrupt:
       print "Bye!"

if __name__ == "__main__":
    main()
