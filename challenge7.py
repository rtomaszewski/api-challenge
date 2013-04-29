#! python -u 

import os
import sys
import time
import getopt
import json
import re
import datetime
import socket

from pprint import pprint
from pprint import pformat

import pyrax
import pyrax.exceptions as exc

import base
from base import ChallengeBase
from base import WaitingForTask
from base import CloudServers
from base import log, debug

import utils

DEBUG = 0

PROGRAM_NAME = "challenge7.py" 

class Challenge7(ChallengeBase): 
    """ 
    Challenge 7: Write a script that will create 2 Cloud Servers and add them as nodes to a new Cloud Load Balancer
    """

    def __init__ (self, debug_level=0, args=[], optlist=[]) :
        ChallengeBase.__init__(self, debug_level)

        self.message ="""
    usage: %s [-h] [-v] 
        -h - usage help 
        -v - verbose / debug output 
    """ % (PROGRAM_NAME)

        self.optlist = optlist
        self.args = args

        self.cs_count = 2
        self.servers = []

        self.nodes=[]
        self.lb=None
        self.lb_name="challenge7-vip"
        self.vip=None

    def check(self):
        debug("check start")

        try:
            self.clb.find(name=self.lb_name) 
            log("found lb %s, please remove it before reruning the script" % self.lb_name )
            ret = False
        except exc.NotFound, e:
            ret = True
        except exc.NoUniqueMatch, e:
            ret = False
            log("more than one lb with name %s found, please remove them before reruning the script" % self.lb_name )

        
        return ret

    def show(self):
        debug("show start")

        lb_properties = [ "name", "status", "created", "virtual_ips", "port", "protocol", "algorithm", "nodeCount" ]
        
        for prop in lb_properties : 
            log("lb %s : %s " % (prop, getattr(self.lb, prop)) )

        for n in self.nodes:
            log("Node: %s" % n.to_dict() )

    def delete_all(self):
        debug("delete_all start")

        for s in self.servers :
            s.delete()
        self.lb.delete()

    def check_lb(self, lb_name ):
        debug("check_lb start")

        self.lb=self.clb.find(name=lb_name) 
        return self.lb.status == "ACTIVE"

    def build_lb(self):
        debug("build_lb start")

        for s in self.servers :
            net = [ i["addr"] for i in s.addresses["private"] ] 
            net = utils.get_ipv4net(net)

            node = self.clb.Node(address=net, port=80, condition="ENABLED")
            self.nodes.append(node)

        self.vip = self.clb.VirtualIP(type="PUBLIC")
        self.lb = self.clb.create(self.lb_name, port=80, protocol="HTTP", nodes=self.nodes, virtual_ips=[self.vip])

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        log("Building %d cloud servers" % self.cs_count)
        
        mycs=CloudServers(self.cs_count, "challenge7")
        self.servers = mycs.get_servers()

        log("Building and configuring lb ...")
        self.build_lb()

        wait = WaitingForTask(self.check_lb, [self.lb_name], sleep_time=5, max_timeout=1)
        if wait.wait_for_tasks() == False: 
            log("Aborting as the build of lb is taking too long; created lb and cloud servers will be deleted")
            self.delete_all()
            sys.exit(-1)

        self.show()

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vhid')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge7(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge7(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
