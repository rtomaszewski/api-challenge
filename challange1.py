import os
import time
import getopt
import sys
import json
import re
import time
import datetime

from pprint import pprint
from pprint import pformat

import pyrax

DEBUG = 0
PROGRAM_NAME="challange1.py"

def log(message):
    t=time.strftime("%H:%M:%S", time.gmtime())
    print("[%s] %s" % (t, message))  

def debug(message):
    if DEBUG>0:
        log("[debug %2d]" % DEBUG + " " + message)

class Challange1:
  """ 
  Challenge 1: Write a script that builds three 512 MB Cloud Servers that following a similar 
  naming convention. (ie., web1, web2, web3) and returns the IP and login credentials for each 
  server. Use any image you want. Worth 1 point 
  """
  
  # for img in cs.images.list():
  #   print img
  #   print img.id
  
  # <Image: Ubuntu 12.04 LTS (Precise Pangolin)>
  # 5cebb13a-f783-4f8c-8058-c4182c724ccd
  ubuntu_1204_id="5cebb13a-f783-4f8c-8058-c4182c724ccd"
  
  # for flavor in cs.flavors.list():
  #   print flavor
  #   print flavor.id
   
  #  <Flavor: 512MB Standard Instance>
  # 2
  flavor_512=2

  SLEEP_TIME=30 #sec
  MAX_TIMEOUT=4 #min
  
  all_built=0
  
  is_timeout=False
  max_time=None
  
  def __init__ (self):
    conf = os.path.expanduser("rackspace_cloud_credentials.txt")
    pyrax.set_credential_file(conf, "LON")
    self.cs = pyrax.cloudservers
  
    self.MAX_SERVERS=3
    self.servers=[]
    self.servers_build_status=[ 0 for i in self._cs_range() ]

  def sleep(self):
    time.sleep(self.SLEEP_TIME)

  def _cs_range(self, count=None):
    if not count :
      count=self.MAX_SERVERS

    return range(0,count)

  def usage(self, message=None):
    if message is not None: 
      print message

    print """
  usage: %s [-h] [-v]
    -h - usage help 
    -v - verbose/debug output
    
    args:
      none
      
    example:
      # run normaly 
      %s

      # run in debug mode 
      %s -v
        
""" % (PROGRAM_NAME, PROGRAM_NAME)

  def is_timeout(self):
    now=datetime.datetime.now()
    if now > self.max_time:
      return True
    else:
      return False

  def set_max_timeout(self):
    if not self.max_time :
      now=datetime.datetime.now()
      delta=datetime.timedelta(minutes=self.MAX_TIMEOUT)
      self.max_time=now + delta

  def check_cs(self):
    """
    return:
      true if all cs are built fine
      false if timeout has been reached or some servers are still in building state
    """
    debug("check_cs start")
    
    for i in self._cs_range() : 
      if self._check_one_cs(i):
        self.servers_build_status[i]=1

    if sum(self.servers_build_status) == self.MAX_SERVERS :
      return True

    return False

  def _check_one_cs(self, nr):
    """
    checks if a cloud server #nr is built 
    return
      true if the cs is build 
      false otherwise 
    """
    
    debug("_check_one_cs start")
    debug("checking %d" % nr)
    
    s=self.servers[nr]
    snew=self.cs.servers.get(s.id)
    if snew.status == "ACTIVE":
      return True

    return False

  def build_servers(self,count=None):
    debug("build_servers start")

    for i in self._cs_range(count) :
      name="web"+str(i)
      log("building %s cloud server" % (name,) )
      s = self.cs.servers.create(name, self.ubuntu_1204_id, self.flavor_512)
      self.servers.append(s)

  def delete_servers(self):
    is_error=False

    for i in self._cs_range() :
      try:
        s=self.servers[i]
        s.delete()
      except Exception, e:
        log("ERROR: couldn't delete server id %d and name %s" % (s.id, s.name) )

  def show(self):
    debug("show start")

    log ("Cloud server details:") 
    for i in self._cs_range() :
      s=self.servers[i]
      ip=s.networks["public"][0]
      print ("Server #%2d:  ID %37s IP %16s password %s" % (i, s.id, ip, s.adminPass) )

  def run(self):
    debug("main start")
    debug("path sys.argv[0]")

    log("Building %d cloud server(s)." % self.MAX_SERVERS)
    self.build_servers()

    log("Waiting for the servers to be built ...")
    
    self.set_max_timeout()
    self.sleep()

    while True: 
      self.check_cs()
      if self.is_timeout() == False : 
         print(".")
         self.sleep()
      else:
        break

    self.show()
    self.delete_servers()
    
if __name__ == '__main__': 
    Challange1().run()
