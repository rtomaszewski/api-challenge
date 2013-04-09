#! python -u 

import os
import sys
import time
import getopt
import sys
import json
import re
import time
import datetime

import pyrax

import base
from base import ChallengeBase
from base import log, debug

PROGRAM_NAME="challenge3.py"

class Challenge3(ChallengeBase): 
    """ 
    Challenge 2: Write a script that accepts a directory as an argument as well as a container name.
    The script should upload the contents of the specified directory to the container (or create it 
    if it doesn't exist). The script should handle errors appropriately. (Check for invalid paths, 
    etc.) Worth 2 Points
    """

    def __init__ (self, MAX_IMAGES=None):
        ChallengeBase.__init__(self)

        message ="""
  usage: %s [-h] [-v] [-d] [-c] [-i] [-u cloud-server-id ]
    -h - usage help 
    -v - verbose / debug output
"""
        self.optlist, self.args = None, None

    def run(self):
        ChallengeBase.run(self)

        optlist, args = getopt.getopt(sys.argv[1:], 'vh:d:c:i:u:')

        debug("options: " + ', '.join( map(str,optlist) ) ) 
        debug("arguments: " + ", ".join(args ))

        for o, val in optlist:
            if o == "-v":
                base.DEBUG=1
            elif o == "-h":
                self.usage()
                sys.exit()



if __name__ == '__main__': 
    try:
        base.DEBUG=1
        chalange=Challenge3()
        chalange.run()
    except Exception, e:
        # chalange.delete_servers()
        # chalange.delete_cloned_servers()
        # chalange.delete_images()
        raise e