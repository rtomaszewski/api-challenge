#! python -u 

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

DEBUG = 1
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
  
  def __init__ (self, MAX_SERVERS=None):
    conf = os.path.expanduser("rackspace_cloud_credentials.txt")
    pyrax.set_credential_file(conf, "LON")
    self.cs = pyrax.cloudservers
  
    if MAX_SERVERS is not None :
      self.MAX_SERVERS=MAX_SERVERS
    else:
      self.MAX_SERVERS=3

    self.servers=[]
    self.servers_build_status=[ 0 for i in self._cs_range() ]

    self.opt_delete_cs=True

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
    -v - verbose / debug output
    -d - doesn't delete cloud servers (you should delete them manually otherwise you will be paying for the resources )
    
    args:
      none
      
    example:
      # create servers, collect details and print them on stdout, at the end delete all created cloud servers
      %s

      # run in debug mode and doesn't delete created cloud servers
      %s -v -d
        
""" % (PROGRAM_NAME, PROGRAM_NAME)

  def is_timeout(self):
    now=datetime.datetime.now()
    if now > self.max_time:
      return True
    else:
      return False

  def is_max_timeout_set(self):
    if self.max_time is None :
      return False

    return True

  def set_max_timeout(self):
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
        self.current_servers_build_status[i]=1

    if sum(self.current_servers_build_status) == self.MAX_SERVERS :
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
    
    s=self.current_servers[nr]
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

  def _delete_servers(self, servers_list):
    debug("_delete_servers start")

    for i in self._cs_range() :
      try:
        s=servers_list[i]
        s.delete()
      except Exception, e:
        log("ERROR: couldn't delete server id %d and name %s" % (s.id, s.name) )

  def delete_servers(self):
    debug("delete_servers start")

    if self.opt_delete_cs == False:
      return

    self._delete_servers(self.servers)

  def show(self):
    self.show_cs()

  def show_cs(self):
    debug("show_cs start")

    log ("Created test cloud server details:") 
    self._show(self.servers)

  def _show(self, servers_list):
    debug("_show start")

    for i in self._cs_range() :
      s=servers_list[i]
      debug(str(s.networks))

      for net in s.networks['public']:
        if '.' in net : 
          ip=net

      print ("Server #%2d:  ID %37s IP %16s password %s" % (i, s.id, ip, s.adminPass) )

  def set_current_build(self, servers_list, servers_list_build_status):
    self.current_servers=servers_list
    self.current_servers_build_status=servers_list_build_status

  def wait_for_build(self, ):
    debug("wait_for_build start")
    
    self.set_max_timeout()
    self.sleep()

    while True: 
      self.check_cs()
      if self.is_timeout() == False : 
         print(".")
         self.sleep()
      else:
        break

  def run(self):
    debug("main start")
    debug("path "+ sys.argv[0])

    optlist, args = getopt.getopt(sys.argv[1:], 'vh:d:')

    debug("options: " + ', '.join( map(str,optlist) ) ) 
    debug("arguments: " + ", ".join(args))

    user, key = None, None
    for o, val in optlist:
      if o == "-v":
        global DEBUG 
        DEBUG = 1
      elif o == "-h":
        self.usage()
        sys.exit()
      elif o =="-d":
        log("cloud servers are not going to be deleted after execution")
        self.opt_delete_cs=False

    log("Building %d cloud server(s)." % self.MAX_SERVERS)
    self.build_servers()

    log("Waiting for the servers to be built ...")
    self.set_current_build(self.servers, self.servers_build_status)
    self.wait_for_build()
    
    self.show()
    self.delete_servers()
    
if __name__ == '__main__': 
    Challange1().run()
