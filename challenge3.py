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

PROGRAM_NAME = "challenge3.py" 

class Challenge3(ChallengeBase): 
    """ 
    Challenge 3: Write a script that accepts a directory as an argument as well as a container name.
    The script should upload the contents of the specified directory to the container (or create it 
    if it doesn't exist). The script should handle errors appropriately. (Check for invalid paths, 
    etc.) Worth 2 Points
    """

    def __init__ (self, MAX_IMAGES=None, debug=0):
        ChallengeBase.__init__(self,debug)

        self.message ="""
    usage: %s [-h] [-v] dir-name container-name
        -h - usage help 
        -v - verbose / debug output 
        dir-name - a path to a directory
        container-name - upload the dir-name to this cloud container
    """ % (PROGRAM_NAME)

        self.optlist, self.args = None, None

    def wait_for_upload(self):
        debug("wait_for_upload start")

        total_bytes = self.total_bytes
        upload_key = self.upload_key

        print "Total bytes to upload:", total_bytes
        uploaded = 0
        while uploaded < total_bytes:
            uploaded = self.cf.get_uploaded(upload_key)
            print "Progress: %4.2f%%" % ((uploaded * 100.0) / total_bytes)
            time.sleep(1)

    def upload_dir(self, path):
        debug("upload_dir start")

        try:
            cont = self.cf.get_container(self.container)
            log("container %s exists, all newly uploaded files will overwrite existing cloud files" %
                self.container)

        except exc.NoSuchContainer, e:
            log("container %s don't exists, create a new one ..." % (self.container,) )
            cont = self.cf.create_container(self.container)
        except Exception, e:
            log('unrecovered error when trying to find container %s' % self.container)
            raise e

        self.upload_key, self.total_bytes = self.cf.upload_folder(self.path, cont)

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
        
        log("Uploading directory %s to container %s" % (self.path, self.container))
        self.upload_dir(self.path) 
        self.wait_for_upload()

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vh')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge3(DEBUG).usage()
            sys.exit()

    challenge = Challenge3(debug=DEBUG)
    challenge.run()
