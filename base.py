#! python -u 

import os
import sys
import time
import getopt
import json
import re
import datetime

from pprint import pprint
from pprint import pformat

import pyrax
import pyrax.exceptions as exc

DEBUG = 0

def log(message):
    t=time.strftime("%H:%M:%S", time.gmtime())
    print("[%s] %s" % (t, message))  

def debug(message):
    global DEBUG
    if DEBUG>0:
        log("[debug %2d]" % DEBUG + " " + message)

class ChallengeBase:
    """ A base file for the challenge classes """

    def __init__ (self, debug):
        self.message=None

        global DEBUG
        DEBUG=debug

        conf = os.path.expanduser("rackspace_cloud_credentials.txt")
        pyrax.set_credential_file(conf, "LON")
        self.cs = pyrax.cloudservers
        self.cf = pyrax.cloudfiles
  
    def usage(self, message=None):
        debug("usage start")
        
        if message is not None: 
            print message
        elif self.message is not None :
            print self.message
        else:
            print("usage: not implemented")

    def run(self):
        debug("base run start")
        debug("path "+ sys.argv[0])


if __name__ == '__main__': 
    challenge=ChallengeBase()
    challenge.run()
