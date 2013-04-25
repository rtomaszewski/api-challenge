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

        self.account_name = pyrax.identity.username

        self.cs = pyrax.cloudservers
        self.cf = pyrax.cloudfiles
        self.dns = pyrax.cloud_dns
        self.cdb = pyrax.cloud_databases
        self.cbs = pyrax.cloud_blockstorage
        self.clb = pyrax.cloud_loadbalancers
  
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
    def __init__(self, check_task_func, resources_list, sleep_time=None, max_timeout=None ):
        self.check_task_func = check_task_func

        if type(resources_list) is not  list :
            self.resources_list = [resources_list]
        else:
            self.resources_list = resources_list

        self.resources_build_status=[ 0 for i in self.res_range() ]

        self.max_time=None

        self.SLEEP_TIME = sleep_time if sleep_time else 30  #sec
        self.MAX_TIMEOUT= max_timeout if max_timeout else 6 #min 

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

class CloudServers(ChallengeBase):
    def __init__(self, count, name_prefix, image=None, flavor=None, files=None) :
        global DEBUG
        debug_level=DEBUG

        ChallengeBase.__init__(self, debug_level)

        self.count = count
        self.name_prefix = name_prefix

        self.servers = []

        self.image = image if image else self.get_image()
        self.flavor = flavor if flavor else self.get_flavor()
        self.files = files

        self.build_cloud_servers(count)

    def check_cs_build(self, cs_obj):
        """ returns True when the cloud is built otherwise False """
        debug("check_cs_build start %s" % cs_obj.name)

        snew=self.cs.servers.get(cs_obj.id)
        return True if snew.status == "ACTIVE" else False

    def get_image(self):
        [ image ] = filter ( lambda x : bool(re.match("Ubuntu 10.04.*" , x.name)), self.cs.images.list())
        return image.id

    def get_flavor(self):
        [ f512 ] = filter( lambda x : x.ram==512 , self.cs.flavors.list())
        return f512.id

    def build_cloud_servers(self, count=0):
        debug("build_cloud_servers start")

        for i in xrange(0, count) :
            name= "%s-%d" % (self.name_prefix, i)

            # debug("name %s image %s flavor %s" % (name, self.image, self.flavor) )
            # pprint(self.files)

            s = self.cs.servers.create(name, self.image, self.flavor, files=self.files)
            self.servers.append(s)

    def delete_cs(self):
        debug("delete_cs start")

        for c in self.servers :
            c.delete()

    def get_servers(self):
        debug("get_servers start")

        wait = WaitingForTask(self.check_cs_build, self.servers)
        if wait.wait_for_tasks() == False: 
            self.delete_cs()
            return None

        servers=[]
        for s in self.servers : 
            servers.append(self.cs.servers.get(s.id))

        return servers
        
if __name__ == '__main__': 
    challenge=ChallengeBase(1)
    challenge.run()
