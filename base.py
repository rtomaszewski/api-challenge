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

    def __init__ (self):
        self.message=None
        
    def usage(self, message=None):
        if message is not None: 
            print message

    def run(self):
        debug("main start")
        debug("path "+ sys.argv[0])


if __name__ == '__main__': 
    chalange=ChallengeBase()
    DEBUG=1
    chalange.run()
