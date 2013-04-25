#! python -u 

import os
import sys
import time
import getopt
import json
import re
import datetime
import socket

from pprint import pprint
from pprint import pformat

import pyrax
import pyrax.exceptions as exc

import base
from base import ChallengeBase
from base import WaitingForTask
from base import CloudServers
from base import log, debug

import utils

DEBUG = 0

PROGRAM_NAME = "challenge10.py" 

class Challenge10(ChallengeBase): 
    """ 
    Challenge 10: Write an application that will:
    - Create 2 servers, supplying a ssh key to be installed at /root/.ssh/authorized_keys.
    - Create a load balancer
    - Add the 2 new servers to the LB
    - Set up LB monitor and custom error page.
    - Create a DNS record based on a FQDN for the LB VIP.
    - Write the error page html to a file in cloud files for backup. Whew! That one is worth 8 points
    """

    def __init__ (self, debug_level=0, args=[], optlist=[]) :
        ChallengeBase.__init__(self, debug_level)

        self.message ="""
    usage: %s [-h] [-v] [-d] [ -s ssh-key ] [ -e error-page ] [ -c container-name ] [ -i image-id ] [ -f flavor-id ] -n FQDN-name  

    image-id -f flavor-id
        -h - usage help 
        -v - verbose / debug output 
        -d - delete objects if they existed in cloud before creating new one
        -n - FQDN name like www.myexample.com
        -s - path to your ssh public key (not priv!)
        -e - path to a html file that will be served from the LB when all pool members are down
        -c - name of cloud files container-name to store the backup data
        -i - specify image-id or use the default for Ubuntu 10.04
        -f - specify flavor-id or use the default for the smallest cloud server
    """ % (PROGRAM_NAME)

        self.optlist = optlist
        self.args = args

        self.opt_delete = False

        self.fqdn_name = None
        self.domain_name = None
        self.domain = None
        self.recs = None

        self.ssh_public_key_name = None
        self.ssh_public_key = None

        self.error_page_name = None
        self.error_page_path = None
        self.error_page = None

        self.container_name = None
        self.container = None

        self.image = None
        self.image_id = None

        self.flavor = None
        self.flavor_id = None

        self.server_prefix=None
        self.cs_count=2
        self.servers = []
        
        self.lb=None
        self.lb_name =None
        self.vip=None
        self.vip_address = None
        self.nodes=[]

        for o, val in optlist:
            if o == "-n":
                self.fqdn_name = val
                self.domain_name =  ".".join( self.fqdn_name.split('.')[1:] )
                self.domain=None
                self.recs = None
            elif o == "-s":
                self.ssh_public_key_name = val
            elif o == "-e":
                self.error_page_path = val
            elif o == "-d":
                self.opt_delete = True
            elif o == "-c":
                self.container_name = val
            elif o == "-i":
                self.image_id = val
            elif o == "-f":
                self.flavor_id = val

        if not self.fqdn_name :
            self.usage()
            sys.exit(-1)

        #default values for some variables 

        if not self.container_name :
            self.container_name = self.fqdn_name 

        self.image = None
        if not self.image_id :
            self.image_id = utils.get_image(self.cs)
        
        self.flavor= None
        if not self.flavor_id :
            self.flavor_id = utils.get_flavor(self.cs)

        self.lb_name = self.fqdn_name

        self.server_prefix = self.fqdn_name

    def check_ssh_pub_key(self):
        debug("check_ssh_pub_key start")
        ret = True

        if self.ssh_public_key_name == None:
            try:
                self.ssh_public_key_name = "%s/.ssh/id_rsa.pub" % os.environ["HOME"]
            except Exception, e:
                ret=False
                log("Please specify a path to ssh public key")
                sys.exit(-1)

        try:
            f = open(self.ssh_public_key_name)
            self.ssh_public_key = f.read()
            
        except Exception, e:
            log("Can't read public ssh key file %s" % self.ssh_public_key_name)

        return ret

    def check_error_page(self):
        debug("check_error_page start")
        ret = True
        
        if self.error_page_path == None:
            self.error_page_path = "error.html"
            self.error_page="<html> <head> <title>Challenge 10 - Default error page on LB</title>\
                            </head><body> Sorry but all pool members failing health cheks. </body></html>"
        self.error_page_name = os.path.basename(self.error_page_path)

        if self.error_page == None :
            try:
                f = open(self.error_page_path)
                self.error_page = f.read()
                
            except Exception, e:
                ret=False
                log("Can't read the customer error page %s" % self.error_page_path)

        return ret

    def check_cloud_servers(self):
        debug("check_cloud_servers start")
        ret = True

        for i in xrange(0, self.cs_count) :
            name= "%s-%d" % (self.server_prefix, i)
            try:
                c=self.cs.servers.find(name=name)
                c.delete()
                log("Deleted existing cloud server %s" % name )
            except Exception, e:
                debug("There is not cs with name %s" % name )
        
        return ret

    def check_fqdn_and_dns(self):
        debug("check_fqdn_and_dns start")
        ret = True

        if len(self.fqdn_name.split('.')) < 3 :
            log("The FQDN is incorrect, example: foo.my-example.com")
            ret=False
            sys.exit(-1)

        try:
            dns=self.dns.find(name=self.domain_name)
            if self.opt_delete :
                log("Deleting existing domain %s" % self.domain_name)
                dns.delete()
            else :
                log("There is domain %s for the FQDM %s you provided; please change the FQDM or delete the domain" %
                    (self.domain_name, self.fqdn_name) )
                ret=False
        except exc.NotFound, e:
            pass

        return ret

    def check_container(self):
        debug("check_container start")
        ret = True

        containers=self.cf.list_containers()
        if self.container_name in containers :
            if self.opt_delete :
                for c in self.cf.get_all_containers() :
                    if c.name == self.container_name :
                        c.delete(del_objects=True)
                        break

                log("Deleted container %s" % self.container_name)
            else :
                log("container %s exists, please remove it and rerun the scrip again" % self.container_name)
                ret = False

        return ret

    def check_existing_lb(self):
        debug("check_existing_lb start")
        ret = True

        try:
            lb=self.clb.find(name=self.lb_name) 
            if self.opt_delete :
                lb.delete()
            else :
                log("found lb %s, please remove it before reruning the script" % self.lb_name )
                ret = False
        except exc.NotFound, e:
            pass
        except exc.NoUniqueMatch, e:
            ret = False
            log("more than one lb with name %s found, please remove them before reruning the script" % self.lb_name )

        return ret

    def check(self):
        debug("check start")
        ret = True

        if self.check_ssh_pub_key() :
            log("Checked your ssh public key %s, ok" % self.ssh_public_key_name )
        else :
            ret=False

        if self.check_error_page() :
            log("Checked your error page %s, ok" % self.error_page_path )
        else :
            ret=False

        if self.check_cloud_servers():
            log("Checked your existing cloud server %s-*, ok" % self.server_prefix )

        if self.check_fqdn_and_dns() : 
            log("Checked your FQDN %s, ok" % self.fqdn_name )
            log("Checked your DNS domains %s, there is none, ok" % self.domain_name )
        else :
            ret=False

        if self.check_container() : 
            log("Checked your container %s where we are going to keep backup data, ok" % self.container_name )
        else :
            ret=False

        if self.check_existing_lb() :
            log("Checked your lb %s, there is none, ok" % self.lb_name )
        else :
            ret=False

        try:
            self.image=self.cs.images.find(id=self.image_id)
            log("Checked your image id %s, ok" % self.image_id )
        except exc.NotFound, e:
            log("The image id is incorrect")
            ret=False

        try:
            self.flavor=self.cs.flavors.find(id=self.flavor_id)
            log("Checked your flavor id %s, ok" % self.flavor_id )
        except exc.NotFound, e:
            log("The flavor id %s is incorrect" % self.flavor_id)
            ret=False

        return ret

    
    def check_lb(self, lb_name ):
        debug("check_lb start")

        self.lb=self.clb.find(name=lb_name) 
        return self.lb.status == "ACTIVE"

    def wait_for_lb_change(self):
        debug("wait_for_lb_change start")

        wait = WaitingForTask(self.check_lb, [self.lb_name], sleep_time=5, max_timeout=1)
        if wait.wait_for_tasks() == False: 
            log("Aborting as the build of lb is taking too long; all created objects will be deleted")
            
            for s in self.servers :
                s.delete()
            self.lb.delete()

            sys.exit(-1)

    def build_lb(self):
        debug("build_lb start")

        for s in self.servers :
            net = [ i["addr"] for i in s.addresses["private"] ] 
            net = utils.get_ipv4net(net)

            node = self.clb.Node(address=net, port=80, condition="ENABLED")
            self.nodes.append(node)

        self.vip = self.clb.VirtualIP(type="PUBLIC")
        self.lb = self.clb.create(self.lb_name, port=80, protocol="HTTP", nodes=self.nodes, virtual_ips=[self.vip])
        self.wait_for_lb_change()

        self.clb.add_health_monitor(self.lb, 'CONNECT', delay=3, timeout=10, attemptsBeforeDeactivation=3)
        self.wait_for_lb_change()

        self.clb.set_error_page(self.lb, self.error_page)
        self.wait_for_lb_change()

    def build_dns(self):
        debug("build_dns start")

        self.domain=self.dns.create(name=self.domain_name, emailAddress="sample@example.edu", ttl=300, comment="challenge10")

        net = self.lb.virtual_ips[0].address
        self.vip_address = utils.get_ipv4net(net)

        cname_rec = {"type": "A",
                    "name": self.fqdn_name,
                    "data": self.vip_address,
                    "ttl": 300,
                    "comment": "challenge10 vip IP"}

        self.recs = self.domain.add_record(cname_rec)

    def backup_to_cloud_files(self):
        debug("backup_to_cloud_files start")

        c=self.cf.create_container(self.container_name)
        c.store_object(self.error_page_name, self.error_page)
        self.container=c

    def show(self):
        debug("show start")

        log("-" * 70)
        log("vip name %s and ip %s" % (self.lb_name, self.vip_address) )
        
        for i in xrange(0, self.cs_count) :
            name= "%s-%d" % (self.server_prefix, i)
            log("cloud server %s added to pool as %s" % (name, self.nodes[i].address) )

        log("Error page is stored in container %s under name %s" % (self.container_name, self.error_page_name) )
        log("to check if the config works try to: curl -v http://%s" % self.vip_address)

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        log("Building %d cloud servers" % self.cs_count)
        files={'/root/.ssh/authorized_keys': self.ssh_public_key }
        mycs=CloudServers(self.cs_count, self.server_prefix, image=self.image_id, flavor=self.flavor_id, 
                files=files )
        self.servers = mycs.get_servers()

        log("Building and configuring lb ...")
        self.build_lb()

        log("Building and configuring dns domain ...")
        self.build_dns()

        log("Backuping files to cloud files ...")
        self.backup_to_cloud_files()

        self.show()

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vhdn:s:e:c:i:f:')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge10(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge10(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
