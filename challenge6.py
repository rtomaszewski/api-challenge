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
from base import log, debug

DEBUG = 0

PROGRAM_NAME = "challenge6.py" 

class Challenge6(ChallengeBase): 
    """ 
    Challenge 6: Write a script that creates a CDN-enabled container in Cloud Files. 
    """

    def __init__ (self, debug_level=0, args=[], optlist=[]) :
        ChallengeBase.__init__(self, debug_level)

        self.message ="""
    usage: %s [-h] [-v] container-name
        -h - usage help 
        -v - verbose / debug output 
        
        container-name - name of the container
    """ % (PROGRAM_NAME)

        self.optlist = optlist
        self.args = args

        try:
            self.container = None
            self.container_name = self.args[0]

        except Exception, e:
            self.container_name = None

    def check(self):
        debug("check start")
        ret = True

        if self.container_name in self.cf.list_containers() :
            self.container = self.cf.get_container(self.container_name)
        else :
            log("Can't find container name %s under your cloud account %s" % (self.container_name, self.account_name))
            return False

        debug("found container %s, objects %s, bytes %s" % (self.container.name, 
            self.container.object_count, 
            self.container.total_bytes))
        
        return ret

    def enable_cdn(self, container_name):
        debug("enable_cdn start")
        ret=True

        container = self.get_container(container_name)
        if container.cdn_enabled == False:
            container.make_public(ttl=1200)
        else:
            log("container %s is alrady CDN enabled")
            ret = False
        
        return ret

    def get_container(self, container_name):
        self.container=self.cf.get_container(container_name)
        return self.container

    def show(self, container_name):
        debug("show start")

        cont=self.get_container(container_name)
        log("cdn_enabled %s" % cont.cdn_enabled)
        log("cdn_ttl %s" % cont.cdn_ttl)
        log("cdn_uri %s" % cont.cdn_uri)
        log("cdn_ssl_uri %s" % cont.cdn_ssl_uri)
        log("cdn_streaming_uri %s" % cont.cdn_streaming_uri)
        log("cdn_ios_uri %s" % cont.cdn_ios_uri)

        return cont

    def show_file_info(self, cf_file):
        debug("show_file_info start")

        log(cf_file.name)
        log( "%s/%s" % (self.container.cdn_uri, cf_file.name) )
        log( "%s/%s" % (self.container.cdn_ssl_uri, cf_file.name) )

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        log("--------------------------------------------")
        log("Container %s info before enabling CDN:" % self.container_name )
        self.show(self.container_name)

        if self.enable_cdn(self.container_name) :
            log("--------------------------------------------")
            log("Container info after enabling CDN:")
            self.container=self.show(self.container_name)

        log("--------------------------------------------")
        log("Example files from the container %s" % self.container.name)
        
        objects=self.container.get_objects()
        if objects : 
            # print example 2 files from the container 
            for index in [ i for i in range(0, len(objects)) if i < 2 ] :
                cf_file=objects[index]

                log("============================================")
                self.show_file_info(cf_file)

        else: 
            log("there are not files in the container")


if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vhid')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge6(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge6(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
