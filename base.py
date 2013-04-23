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
        self.dns = pyrax.cloud_dns
        self.cdb = pyrax.cloud_databases
        self.cbs = pyrax.cloud_blockstorage
  
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

class WaitingForTask:
    def __init__(self, check_task_func, resources_list ):
        self.check_task_func = check_task_func

        self.resources_list=resources_list
        self.resources_build_status=[ 0 for i in self.res_range() ]

        self.max_time=None
        self.SLEEP_TIME=30 #sec
        self.MAX_TIMEOUT=6 #min

    def set_max_timeout(self, minutes=0):
        if not minutes: minutes=self.MAX_TIMEOUT

        now=datetime.datetime.now()
        delta=datetime.timedelta(minutes=minutes)
        self.max_time=now + delta
    
    def res_range(self, count=None):
        if not count :
            count=len(self.resources_list)
        
        return xrange(0, count)

    def is_timeout(self):
        now=datetime.datetime.now()
        if now > self.max_time:
            return True
        else:
            return False

    def sleep(self):
        time.sleep(self.SLEEP_TIME)

    
    def check_tasks(self):
        """
        return:
            true if all cs are built fine
            false if timeout has been reached or some servers are still in building state
        """
        debug("check_tasks start")
        
        for i, res in enumerate(self.resources_list ) : 
            if self.check_task_func(res):
                self.resources_build_status[i]=1

        if sum(self.resources_build_status) == len(self.resources_list) :
            return True

        return False

    def wait_for_tasks(self):
        """ returns True if the build is successful other wise False """
        debug("wait_for_tasks")
        
        self.set_max_timeout()

        start=datetime.datetime.now()
        self.sleep()

        ret=True
        
        while self.check_tasks() == False :
            if self.is_timeout() == False : 
                print(".")
                self.sleep()
            else:
                log("timeout reached, canceling")
                ret=False
                break

        stop=datetime.datetime.now()
        delta= stop - start
        debug("waited for %s" % delta)

        return ret

if __name__ == '__main__': 
    challenge=ChallengeBase()
    challenge.run()
