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

PROGRAM_NAME = "challenge8.py" 

class Challenge8(ChallengeBase): 
    """ 
    Challenge 8: Write a script that will create a static webpage served out of Cloud Files. The script must
    create a new container, cdn enable it, enable it to serve an index file, create an index file object, 
    upload the object to the container, and create a CNAME record pointing to the CDN URL of the container
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

        self.container_name = "challenge8"
        self.container = None
        self.index_name = "index.html"
        self.index_file_data = "Hello challenge8, it works!\n"

        self.domain_name = "rado-challenge.org"
        self.domain = None
        self.recs = None

        self.rec_CNAME = None
        self.rec_CNAME_data = None
        

    def check(self):
        debug("check start")
        ret = True
 
        containers=self.cf.list_containers()
        if self.container_name in containers :
            log("container %s exists, please remove it and rerun the scrip again" % self.container_name)
            ret = False

        try:
            self.dns.find(name=self.domain_name)
            log("Found domain %s, please delete it and rerun the script" % self.domain_name)
            ret = False
        except exc.NotFound as e:
            pass
        
        return ret

    def show(self):
        debug("show start")

        log("Static site details: (make sure you point your DNS to Rackspace Cloud DNS servers):")
        log("ping %s" % self.rec_CNAME)
        log("curl -v http://%s/%s" % (self.rec_CNAME, self.index_name) )
        log("curl -v http://%s" % (self.rec_CNAME_data) )

    def set_container(self):
        debug("set_container start")

        fname = self.index_name

        c=self.cf.create_container(self.container_name)
        c.store_object(fname, self.index_file_data)
        c.make_public(ttl=300)
        c.set_web_index_page(fname)

        self.container=c

    def set_dns(self):
        debug("set_dns start")

        log("Creating DNS domain %s and setting CNAME records" % self.domain_name)

        self.rec_CNAME = self.container_name + "." + self.domain_name
        self.rec_CNAME_data = self.container.cdn_uri.partition("//")[2]

        domain=self.dns.create(name=self.domain_name, emailAddress="sample@example.edu", ttl=300, comment="challenge8 domain")
        cname_rec = {"type": "CNAME",
                    "name": self.rec_CNAME,
                    "data":  self.rec_CNAME_data,
                    "ttl": 300,
                    "comment": "cloud files CDN enabled container"}
        self.recs = domain.add_record(cname_rec)
        self.domain = domain

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        log("Creating container %s and uploading small %s file." %  (self.container_name, self.index_name) )
        self.set_container()
        self.set_dns()
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
            Challenge8(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge8(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
