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
from pprint import pprint
from pprint import pformat

import pyrax

# sys.path.append(os.path.dirname(__file__))
# print sys.path

from challenge1 import Challenge1

DEBUG = 1
PROGRAM_NAME="challenge2.py"

def log(message):
    t=time.strftime("%H:%M:%S", time.gmtime())
    print("[%s] %s" % (t, message))  

def debug(message):
    if DEBUG>0:
        log("[debug %2d]" % DEBUG + " " + message)

class Challenge2(Challenge1):
    """ 
    Challenge 2: Write a script that clones a server (takes an image and deploys 
    the image as a new server). Worth 2 Point
    """

    def __init__ (self, MAX_IMAGES=None):
        Challenge1.__init__(self, 1)

        # self.MAX_IMAGES=self.MAX_SERVERS

        self.images=[]
        self.images_obj=[ None for i in self._cs_range() ]
        self.images_build_status=[ 0 for i in self._cs_range() ]

        self.cloned_servers=[]    
        self.cloned_servers_build_status=[ 0 for i in self._cs_range() ]

        self.opt_delete_clones=True
        self.opt_delete_images=True

        self.cloud_id=None

      # def _image_range(self, count=None):
      #   if not count :
      #     count=self.MAX_IMAGES

      #   return range(0,count)

    def usage(self, message=None):
        if message is not None: 
            print message

        print """
  usage: %s [-h] [-v] [-d] [-c] [-i] [-u cloud-server-id ]
    -h - usage help 
    -v - verbose / debug output
    -d - doesn't delete cloud servers (you should delete them manually otherwise you will be paying for the resources )
    -c - doesn't delete cloned cloud servers 
    -i - doesn't delete images
    -u - use this cloud server to clon from (don't create any cloud servers)
    
    args:
      none
      
    example:
      # create servers, collect details and print them on stdout, at the end delete all created cloud servers
      %s

      # run in debug mode and don't delete created cloud servers
      %s -v -d
        
""" % (PROGRAM_NAME, PROGRAM_NAME)

    def show(self):
        debug("show start")
        
        log ("Created cloud server details:") 
        self.show_cs(self.servers)

        log ("Created images details:") 
        self.show_images()

        log ("Created cloned server details:") 
        self.show_clones()

    def show_images(self, image_list=None):
        debug("show_images start")

        if not image_list : image_list=self.images_obj

        for i in self._cs_range() :
          img=image_list[i]
          print ("Image  #%2d:  ID %37s name %16s from server %s" % (i, img.id, img.name, img.server["id"]) )

    def show_clones(self, servers_list=None):
        debug("show_clones start")

        if not servers_list : servers_list=self.cloned_servers
        self.show_cs(servers_list)

    def find_cloud(self, id):
        try:
            s=self.cs.servers.get(id)
            for i in self._cs_range():
                self.cloned_servers.append(s)

        except Exception, e:
            log("couldn't find cloud server id")
            raise e

    def build_servers_from_image(self, count=None):
        debug("build_servers_from_image start")

        for i in self._cs_range(count) :
            s=self.servers[i]
            img=self.images_obj[i]

            t=datetime.datetime.now()
            # '4.16.22.58.29'
            # d.m.h.m.s
            date_str=".".join(map (str, [t.month,t.day,t.hour,t.minute,t.second]))

            name=s.name
            name_new=name + "_" +date_str

            log("building new %s cloud server from image %s" % (name_new, img.name) )
            
            new_s = self.cs.servers.create(name_new, img.id, self.flavor_512)
            self.cloned_servers.append(new_s)

    def check_one_clone(self, nr):
        debug("check_one_clone start")

        debug("checking %d" % nr)
        
        clone_id=self.current_items[nr]
        i=self.cs.images.get(clone_id)
        self.images_obj[nr]=i

        debug("checking %d status %s progress %d " % (nr, i.status, i.progress))

        if i.status == "ACTIVE":
          return True
        
        return False

    def wait_for_cloning(self):
        debug("wait_for_cloning start")
        
        start=datetime.datetime.now()
        self.set_max_timeout()
        self.sleep()

        ret=self._wait_for_tasks(self.check_one_clone)

        stop=datetime.datetime.now()
        delta= stop - start
        debug("waited for %s" % delta)
        
        return ret

    def clone(self):
        debug("clone start")

        for i in self._cs_range() :
            s=self.servers[i]
            image_name=s.name+'-img'

            log("Creating cloud image file: '%s' from %s cloud server" % (image_name, s.name))

            img=s.create_image(image_name)
            # img = cs.servers.create_image(s.id, image_name)

            self.images.append(img) 

            debug("image id is %s" % (img))      

    def delete_images(self):
        debug("delete_images start")

        if self.opt_delete_images == False:
            return

        for i in self._cs_range() :
          try:
            img=self.images[i]
            self.cs.images.delete(img.id)
          except Exception, e:
            log("ERROR: couldn't delete image file id %d and name %s" % (img.id, img.name) )

    def delete_cloned_servers(self):
        debug("delete_cloned_servers start")

        if self.opt_delete_clones is False :
            return
    
        self.delete_servers(self.cloned_servers) 

    def run(self):
        debug("main start")
        debug("path "+ sys.argv[0])

        optlist, args = getopt.getopt(sys.argv[1:], 'vh:d:c:i:u:')

        debug("options: " + ', '.join( map(str,optlist) ) ) 
        debug("arguments: " + ", ".join(args ))

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
            elif o =="-c":
                log("cloned cloud servers are not going to be deleted after execution")
                self.opt_delete_clones=False
            elif o =="-i":
                log("cloud images are not going to be deleted after execution")
                self.opt_delete_images=False
            elif o =="-u":
                self.cloud_id=val
                self.opt_delete_cs=False
                log("I'm going to use cloud server id %s to create clones" % (self.cloud_id))

        log("Building %d cloud server(s)." % self.MAX_SERVERS)
        if self.cloud_id == None:
            self.build_servers()

            log("Waiting for the servers to be built ...")
            self.set_current_build(self.servers, self.servers_build_status)
            if self.wait_for_build()  is False :
                self.delete_servers()
                sys.exit(-1)

        else:
            self.find_cloud(self.cloud_id)

        log("Preparing to clone %d server(s) ..." % (self.MAX_SERVERS))
        self.clone()
        
        log("Waiting for the clone images to be created ...")
        self.set_current_build(self.images, self.images_build_status)    
        self.wait_for_cloning()

        log("Building %d new cloud server(s) from taken images." % self.MAX_SERVERS)
        self.build_servers_from_image()
         
        log("Waiting for the servers to be built from the cloned images ...")         
        self.set_current_build(self.cloned_servers, self.cloned_servers_build_status)    
        self.wait_for_build()

        self.show()

        self.delete_servers()
        self.delete_cloned_servers()
        self.delete_images()

if __name__ == '__main__': 
    # try:
        challenge=Challenge2()
        challenge.run()
    # except Exception, e:
    #     chalange.delete_servers()
    #     # chalange.delete_cloned_servers()
    #     # chalange.delete_images()
    #     raise e
