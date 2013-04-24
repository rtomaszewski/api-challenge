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

PROGRAM_NAME = "challenge9.py" 

class Challenge9(ChallengeBase): 
    """ 
    Challenge 9: Write an application that when passed the arguments FQDN, image, and flavor 
    it creates a server of the specified image and flavor with the same name as the fqdn,
    and creates a DNS entry for the fqdn pointing to the server's public IP
    """

    def __init__ (self, debug_level=0, args=[], optlist=[]) :
        ChallengeBase.__init__(self, debug_level)

        self.message ="""
    usage: %s [-h] [-v] -n FQDN-name -i image-id -f flavor-id
        -h - usage help 
        -v - verbose / debug output 
        -n - FQDN name
        -i - proper image id
        -f - flavor id 
    """ % (PROGRAM_NAME)

        self.optlist = optlist
        self.args = args

        self.server = None
        self.image = None
        self.flavor = None

        for o, val in optlist:
            if o == "-n":
                self.fqdn_name = val
                self.domain_name =  ".".join( self.fqdn_name.split('.')[1:] )
                self.domain=None
                self.recs = None
                self.net=None

            elif o == "-i":
                self.image_id = val
            elif o == "-f":
                self.flavor_id = val

    def check(self):
        debug("check start")
        ret = True
    
        try:
            self.image=self.cs.images.find(id=self.image_id)
        except exc.NotFound, e:
            log("The image id is incorrect")
            ret=False

        if len(self.fqdn_name.split('.')) < 3 :
            log("The FQDN is incorrect, example: foo.my-example.com")
            ret=False

        try:
            self.dns.find(name=self.domain_name)
            log("There is domain %s for the FQDM %s you provided; please change the FQDM or delete the domain" %
                (self.domain_name, self.fqdn_name) )
            ret=False
        except exc.NotFound, e:
            pass

        try:
            self.flavor=self.cs.flavors.find(id=self.flavor_id)
        except exc.NotFound, e:
            log("The flavor id %s is incorrect" % self.flavor_id)
            ret=False

        return ret

    def check_cs_build(self, cs_obj):
        """ returns True when the cloud is built otherwise False """
        debug("check_cs_build start %s" % cs_obj.name)

        snew=self.cs.servers.get(cs_obj.id)
        return True if snew.status == "ACTIVE" else False

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        log("Creating new DNS zone %s" % self.domain_name)
        self.domain=self.dns.create(name=self.domain_name, emailAddress="sample@example.edu", ttl=300, comment="challenge9 domain")

        log("Creating cloud server ...(please wait the build can take a while)")
        self.server=self.cs.servers.create(name=self.fqdn_name, flavor=self.flavor_id, image=self.image_id)

        wait = WaitingForTask(self.check_cs_build, self.server)
        if wait.wait_for_tasks() == False: 
            log("Cloud server build failed, deleting created objects")
            self.server.delete()
            self.domain.delete()
            sys.exit(-1)

        # get all public IPs
        net = [ i["addr"] for i in self.server.addresses["public"] ] 
        self.net = utils.get_ipv4net(net)

        cname_rec = {"type": "A",
                    "name": self.fqdn_name,
                    "data": self.net,
                    "ttl": 300,
                    "comment": "challenge9 rec"}

        self.recs = self.domain.add_record(cname_rec)

        log("DNS zone %s has been udpated and a new A record created" % (self.domain_name))
        log("rec A: %s -> %s" % (self.fqdn_name, self.net))

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vhn:i:f:')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge9(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge9(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
