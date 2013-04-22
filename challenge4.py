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

import base
from base import ChallengeBase
from base import log, debug

DEBUG=0

PROGRAM_NAME = "challenge4.py" 

class Challenge4(ChallengeBase): 
    """ 
    Challenge 4: Write a script that uses Cloud DNS to create a new A record when passed a FQDN
    and IP address as arguments. 
    """

    def __init__ (self, MAX_IMAGES=None, debug=0):
        ChallengeBase.__init__(self,debug)

        self.message ="""
    usage: %s [-h] [-v] FQDN ip-add
        -h - usage help 
        -v - verbose / debug output 
        FQDN - Fully Qualified Domain Name; exaple www.wikipedia.org
        ip-add - ip address
    """ % (PROGRAM_NAME)

        self.optlist, self.args = None, None


    def check_path(self, path):
        return os.path.isdir(path)

    def check_container(self, container):
        return bool(re.match('^[a-z0-9\\\\]+$', container, re.IGNORECASE))

    def check(self, args):
        debug("check start")
        ret=True

        try:
            self.path=args[0]
            self.container=args[1]

            if self.check_path(self.path) == False: 
                log("Invalid directory path string (check if the path directory exists and has alphanumeric characters only")
                ret=False
            
            if self.check_container(self.container) == False:
                log("Container name has invalid chars")
                ret=False

        except Exception, e:
            ret=False
            log("missing params")

        return ret


    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check(args) is False:
            self.usage()
            sys.exit(-1)
        

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vh')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge4(DEBUG).usage()
            sys.exit()

    challenge = Challenge4(debug=DEBUG)
    challenge.run()
