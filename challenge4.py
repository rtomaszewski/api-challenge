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
from base import log, debug

DEBUG = 0

PROGRAM_NAME = "challenge4.py" 

class Challenge4(ChallengeBase): 
    """ 
    Challenge 4: Write a script that uses Cloud DNS to create a new A record when passed a FQDN
    and IP address as arguments. 
    """

    def __init__ (self, MAX_IMAGES=None, debug=0, args=[], optlist=[]):
        ChallengeBase.__init__(self, debug)

        self.message ="""
    usage: %s [-h] [-v] [-d] FQDN ip-add
        -h - usage help 
        -v - verbose / debug output 
        -d - if a domain exists it will be deleted first 

        FQDN - Fully Qualified Domain Name; exaple www.wikipedia.org
        ip-add - ip address
    """ % (PROGRAM_NAME)

        self.optlist = optlist
        self.args = args
        
        self.opt_delete_domain = False

        if "-d" in map(lambda x: x[0], optlist) :
            self.opt_delete_domain = True

        try:
            self.domain_name = self.args[0]
            self.domain = None

            self.ip_str = self.args[1]

        except Exception, e:
            log("missing params")
            self.usage()
            sys.exit(-1)


    def check_domain_name(self, domain_name):
        return bool(re.match('^[a-z0-9.-]+$', domain_name, re.IGNORECASE))

    def convert_ip(self, ip_str):
        return socket.inet_ntoa( socket.inet_aton(ip_str) )

    def check_ip(self, ip_str):
        try:
            socket.inet_aton(ip_str)
        except socket.error:
            return False

        return True

    def check(self):
        debug("check start")
        ret = True

        if self.check_domain_name(self.domain_name) == False: 
            log("Invalid domain name string")
            ret = False
        
        if self.check_ip(self.ip_str) == False:
            log("Invalid ip address")
            ret = False
        else :
            self.ip_str = self.convert_ip(self.ip_str)
            
        return ret

    def create_domain(self, domain_name):
        debug("create_domain start")
        
        try:
            dom = self.dns.find(name=domain_name)
            if self.opt_delete_domain :
                debug("deleting domain %s" % domain_name)
                dom.delete()
            else:
                log("Domain %s exists, please specify other domain name or use -d option" % domain_name)
                return False

        except exc.NotFound:
            pass

        try:
            dom = self.dns.create(name=domain_name, emailAddress="sample@challenge4.edu",
                    ttl=900, comment="challenge4 domain")
        except exc.DomainCreationFailed as e:
            log("Domain creation failed: %s" % e)
            return False

        self.domain = dom
        log("Domain created: %s" % domain_name)

        return True

    def create_record(self, domain_name, ip_str) :
        debug("create_record start")

        # Substitute your actual domain name and IP addresses here
        a_rec = {"type": "A",
                "name": domain_name,
                "data": ip_str,
                "ttl": 6000
                }

        log("Adding records to our domain ...")
        recs = self.domain.add_records([a_rec])

        return True

    def show(self):
        debug("show start")

        dom = self.dns.find(name=self.domain_name)

        log("domain name: %s created at %s" % (dom.name, dom.created) )
        for r in dom.list_records() : 
            log("record %3s %s -> %s" % (r.type, r.name, r.data) )

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)
        
        if self.create_domain(self.domain_name) == False:
            self.usage()
            sys.exit(-1)    

        if self.create_record(self.domain_name, self.ip_str) :
            self.show()

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vhd')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge4(DEBUG).usage()
            sys.exit()

    challenge = Challenge4(debug=DEBUG, args=args, optlist=optlist)
    challenge.run()
