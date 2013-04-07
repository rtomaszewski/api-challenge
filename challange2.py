import os
import time
import getopt
import sys
import json
import re
import time
import datetime

import pyrax

DEBUG = 1
PROGRAM_NAME="challange2.py"

def log(message):
    t=time.strftime("%H:%M:%S", time.gmtime())
    print("[%s] %s" % (t, message))  

def debug(message):
    if DEBUG>0:
        log("[debug %2d]" % DEBUG + " " + message)

class Challange2:
  """ 
  Challenge 2: Write a script that clones a server (takes an image and deploys 
  the image as a new server). Worth 2 Point
  """

  ubuntu_1204_id="5cebb13a-f783-4f8c-8058-c4182c724ccd"
  flavor_512=2

  SLEEP_TIME=30 #sec
  MAX_TIMEOUT=4 #min
  
  # all_built=0
  
  is_timeout=False
  max_time=None

  def __init__ (self):
    conf = os.path.expanduser("rackspace_cloud_credentials.txt")
    pyrax.set_credential_file(conf, "LON")
    self.cs = pyrax.cloudservers

    self.MAX_SERVERS=1
  
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

  def _cs_range(self, count=None):
    if not count :
      count=self.MAX_SERVERS

    return range(0,count)

  def set_max_timeout(self):
    if not self.max_time :
      now=datetime.datetime.now()
      delta=datetime.timedelta(minutes=self.MAX_TIMEOUT)
      self.max_time=now + delta

  def build_servers(self):
  	debug("build_servers start")

    for i in self._cs_range(count) :
      name="challange2"+str(i)
      log("building %s cloud server" % (name,) )
      s = self.cs.servers.create(name, self.ubuntu_1204_id, self.flavor_512)
      self.servers.append(s)

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

  def wait_for_server(self):
  	debug("wait_for_server start")
  	
    log("Waiting for the %d server(s) to be built ..." % (self.MAX_SERVERS) )
    
    self.set_max_timeout()
    self.sleep()

    while True: 
      self.check_cs()
      if self.is_timeout() == False : 
         print(".")
         self.sleep()
      else:
        break


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

  def run(self):
    debug("main start")
    debug("path "+"sys.argv[0]")

    log("Building %d cloud server(s)." % self.MAX_SERVERS)
    self.build_servers()

    self.show()

if __name__ == '__main__': 
	try:
		chalange=Challange2()
		chalange.run()
	except Exception, e:
		chalange.delete_servers()
		raise e

