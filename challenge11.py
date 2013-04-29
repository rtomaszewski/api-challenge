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

import novaclient.exceptions as exc_nova

import base
from base import ChallengeBase
from base import WaitingForTask
from base import CloudServers
from base import log, debug

import utils

DEBUG = 0

PROGRAM_NAME = "challenge11.py" 

class Challenge11(ChallengeBase): 
    """ 
    Challenge 11: Write an application that will: Create an SSL terminated load balancer 
    (Create self-signed certificate).
    Create a DNS record that should be pointed to the load balancer. Create Three servers 
    as nodes behind the LB.

    Each server should have a CBS volume attached to it. (Size and type are irrelevant.)
    All three servers should have a private Cloud Network shared between them.
    Login information to all three servers returned in a readable format as the result 
    of the script, including connection information. Worth 6 points
    """

    def __init__ (self, debug_level=0, args=[], optlist=[]) :
        ChallengeBase.__init__(self, debug_level)

        self.message ="""
    usage: %s [-h] [-v] [-d] [ -k key-key  ] [ -c cert ] [ -i image-id ]\
[ -f flavor-id ] -n FQDN-name  

    image-id -f flavor-id
        -h - usage help 
        -v - verbose / debug output 
        -d - delete objects if they existed in cloud before creating new one
        -k - certificate pritate key (see -c below)
        -c - public certificate ( see -k above)
        -n - FQDN name like www.myexample.com
        -i - specify image-id or use the default for Ubuntu 10.04
        -f - specify flavor-id or use the default for the smallest cloud server
    """ % (PROGRAM_NAME) 

        self.cert_use_default = False
        self.cert_key_name = None
        self.cert_key = None
        self.cert_name = None
        self.cert = None

        self.opt_delete = False

        self.fqdn_name = None
        self.domain_name = None
        self.domain = None
        self.recs = None

        self.lb=None
        self.lb_name = None
        self.vip=None
        self.vip_address = None
        self.nodes=[]

        self.image = None
        self.image_id = None

        self.flavor = None
        self.flavor_id = None

        self.server_prefix=None
        self.cs_count=3
        self.server_passord = "SecretP@ss1"
        self.servers = []

        self.storage_name = None
        self.volumes=[]

        self.network_name = None
        self.network_range = "192.168.100.0/24"
        self.network = None
        self.network_id = None


        for o, val in optlist:
            if o == "-n":
                self.fqdn_name = val
                self.domain_name =  ".".join( self.fqdn_name.split('.')[1:] )
                self.domain=None
                self.recs = None
            elif o == "-d":
                self.opt_delete = True
            elif o == "-i":
                self.image_id = val
            elif o == "-f":
                self.flavor_id = val
            elif o == "-k":
                self.cert_key_name = val
            elif o == "-c":
                self.cert_name = val
            elif o == "-i":
                self.image_id = val
            elif o == "-f":
                self.flavor_id = val

        if not self.fqdn_name :
            self.usage()
            sys.exit(-1)

        #default values for some variables 

        self.image = None
        if not self.image_id :
            self.image_id = utils.get_image(self.cs)
        
        self.flavor= None
        if not self.flavor_id :
            self.flavor_id = utils.get_flavor(self.cs)

        self.lb_name = self.fqdn_name
        self.storage_name = self.fqdn_name
        self.server_prefix = self.fqdn_name
        self.network_name = self.fqdn_name

        if not self.cert_key_name and not self.cert_name :
            self.cert_use_default = True
            self.cert_key_name = self.fqdn_name + ".key"
            self.cert_key="""-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQCypZq3lUHWhBjDxV6hOtOQFI3WvcGlp9RP+ZHVTcwDb/buaGIL
99xCUabM5TIjzfSMthddEb+43RIdZeaXSnqV0Ut+xF9fPIHiky+DrOS2i77ltu67
RGTerezjM36D4TW5N3vQOR+qIezp1yko1qJr5hROp2ykqcgIL5GzR4980QIDAQAB
AoGBAKIZyKDqa3pGFN6XWf18jnn/XJDNUEiLWAhVkfF2DTfVQcAksUrg1ljLFEp5
chyxBkUj+WE2+Lu6xXQtgaYoK7/+mRRpKEZ6aHEsd5KqoVgxp2igyRZOGyVWaAJ3
loi+GmMiRkjC6o6xxNGG7UNfXSACfbB8eEBaGw61ZhbZJ28NAkEA5rVk/mqQFYzO
WynHT1DUz4YeIpj1ZAnhjn/957knU61VoAjeruLANOmN5bQ2gCKJm7MsPJ11iAdp
Cfltaprq7wJBAMY7Jp0hQBWOp3J1VNTkeG23At/ZQv5QzkUih2hcHjXy54RYqFe/
pIH9qrLC01BjhG2PePrJwaKMmhl7TvQ7FD8CQHmG7848n+1aIJFQ7pZPQ+qVAWbE
H+80bUY9EahwldC0K7iDM5n4A7tbk81+In9Yshf8R78eSnz/Oktwwjw3oq0CQEyZ
3PEJQUdTSdeMCYz/AJ59AwpXXXEC7sJ+dk7YkgAM7nQRAnRuJPbqfET5zkiZPDpO
H9ThlAbpSD8ijD8KeWcCQBxun2xWhCH19BulbUufsocKrwaxAijJ4pc5fX+cabEU
Na05oMyXQxN2tR4gWlbyVrGuZPVRDH39oRej5z2/JUA=
-----END RSA PRIVATE KEY-----
"""
        self.cert_name = self.fqdn_name + ".crt"
        self.cert = """-----BEGIN CERTIFICATE-----
MIICRTCCAa4CCQDcUiuf5f4k5zANBgkqhkiG9w0BAQUFADBnMQswCQYDVQQGEwJB
VTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50ZXJuZXQgV2lkZ2l0
cyBQdHkgTHRkMSAwHgYDVQQDDBdjaGFsbGVuZ2UxMS5leGFtcGxlLm9yZzAeFw0x
MzA0MjgyMjIwMTdaFw0xNDA0MjgyMjIwMTdaMGcxCzAJBgNVBAYTAkFVMRMwEQYD
VQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBXaWRnaXRzIFB0eSBM
dGQxIDAeBgNVBAMMF2NoYWxsZW5nZTExLmV4YW1wbGUub3JnMIGfMA0GCSqGSIb3
DQEBAQUAA4GNADCBiQKBgQCypZq3lUHWhBjDxV6hOtOQFI3WvcGlp9RP+ZHVTcwD
b/buaGIL99xCUabM5TIjzfSMthddEb+43RIdZeaXSnqV0Ut+xF9fPIHiky+DrOS2
i77ltu67RGTerezjM36D4TW5N3vQOR+qIezp1yko1qJr5hROp2ykqcgIL5GzR498
0QIDAQABMA0GCSqGSIb3DQEBBQUAA4GBABVi7jbbZt+6HWFCnGKQOEtpe4uFCXyv
mUh4J06gfbsIs/GbnXzhnGeXGiP/gFoHOqBlyHIAiOUEiLC8idG6DMlGDXpEJABk
/q9BZ4H7ZxAMtsDfGDPU/lFCPoXpm8vBAUPWLS3sM11RzLu6ml+CXeGQOP2gOcnX
bVXe8dPGQeEG
-----END CERTIFICATE-----
"""

    def check_cert(self):
        debug("check_cert start")
        ret = True

        if self.cert_use_default : 
            return True

        try:
            f = open(self.cert_key_name)
            self.cert_key = f.read()
            f.close()
        except Exception, e:
            log("Can't read or the private key file has incorrect data %s" % self.cert_key_name)
            log(e)
            ret = False

        try:
            f = open(self.cert_name)
            self.cert = f.read()
            f.close()
        except Exception, e:
            log("Can't read or the certificate file or it has incorrect data %s" % self.cert_name)
            log(e)
            ret = False

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

    def check_existing_lb(self):
        debug("check_existing_lb start")
        ret = False
        again = 0

        while ret == False and again < 2:
            try:
                lb=self.clb.find(name=self.lb_name) 
                if self.opt_delete :
                    lb.delete()
                    ret=True
                else :
                    log("found lb %s, please remove it before reruning the script" % self.lb_name )
                    ret = False
            except exc.NotFound, e:
                ret=True
            except exc.NoUniqueMatch, e:
                ret = False
                log("more than one lb with name %s found, please remove them before reruning the script" % self.lb_name )
            except exc.BadRequest, e:
                debug("Something went wrong, will retry again")
                time.sleep(5)
                ret=False

            again += 1

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
            except Exception, e: # this is ugly hack as we don't import the nova exceptions 
                debug("There is not cs with name %s" % name )
        
        return ret

    def check_blocks(self) :
        debug("check_storage start")
        ret = True

        for i in xrange(0, self.cs_count) :
            name="%s-%d" % (self.storage_name, i)
            try:
                storage=self.cbs.find(name=name)
                storage.delete()
                log("Deleted existing block storage image  %s" % name )
            except Exception, e:
                debug("There is not block storage with name %s" % name )

        return ret

    def check_network_objects(self):
        debug("check_network_objects start")

        for net in self.cnw.list() :
            if net.name == self.network_name :
                log("Deleted existing network obj %s" % self.network_name)
                net.delete()

        return True
        
    def check(self):
        debug("check start")
        ret = True

        if self.check_cert() :
            log("Checked your cert/key pair %s/%s, ok" % (self.cert_name, self.cert_key_name))
        else :
            ret=False
        
        if self.check_fqdn_and_dns() : 
            log("Checked your FQDN %s, ok" % self.fqdn_name )
            log("Checked your DNS domains %s, there is none, ok" % self.domain_name )
        else :
            ret=False


        if self.check_cloud_servers():
            log("Checked your existing cloud server %s-*, ok" % self.server_prefix )

        if self.check_blocks() :
            log("Checked your block images %s, there is none, ok" % self.storage_name )
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

        if self.check_network_objects():
            log("Checked your existing network objects %s, ok" % self.network_name )

        return ret

    def show(self):
        debug("show start")

        log("-" * 70)
        log("vip name %s and ip %s" % (self.lb_name, self.vip_address) )
        
        for i in xrange(0, self.cs_count) :
            name= "%s-%d" % (self.server_prefix, i)
            log("cloud server %s added to pool as %s" % (name, self.nodes[i].address) )

        log("-" * 70)
        for i, s in enumerate(self.servers) :
            s.change_password(self.server_passord)
            
            net = [ a["addr"] for a in s.addresses["public"] ] 
            net = utils.get_ipv4net(net)

            priv = [ a["addr"] for a in s.addresses[self.network_name] ] 
            priv = utils.get_ipv4net(priv)

            print ("Server #%2d: ID %s name %s pub IP %s priv IP %s password %s" % (i, s.id, 
                s.name, net, priv, self.server_passord) )

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

        debug("key")
        debug(self.cert_key)

        debug("crt")
        debug(self.cert)

        self.lb.add_ssl_termination(
            securePort=443,
            enabled=True,
            secureTrafficOnly=False,
            certificate=self.cert,
            privatekey=self.cert_key )

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
                    "comment": "challenge11 vip IP"}

        self.recs = self.domain.add_record(cname_rec)


    def check_storage(self, volume):
        debug("check_storage start")

        v=self.cbs.find(id=volume.id)
        return v.status == "in-use"

    def wait_for_storage_to_be_attached(self):
        debug("wait_for_storage_to_be_attached start")

        wait = WaitingForTask(self.check_storage, self.volumes, sleep_time=30, max_timeout=5)
        if wait.wait_for_tasks() == False: 
            log("Aborting as the build of block images is taking too long")
            
            for s in self.servers :
                s.delete()

            for v in self.volumes :
                v.delete()

            self.lb.delete()

            sys.exit(-1)

    def build_cs(self):
        debug("build_cs start")

        self.network=self.cnw.create(self.network_name, cidr=self.network_range)
        self.network_id = self.network.get_server_networks(public=True, private=True)

        vols=[]
        for i in range(0, self.cs_count) :
            name="%s-%d" % (self.storage_name, i)
            vol = self.cbs.create(name=name, size=100, volume_type="SATA")
            vols.append(vol)

        self.volumes = vols

        mycs=CloudServers(self.cs_count, self.server_prefix, image=self.image_id, 
                flavor=self.flavor_id,
                nics=self.network_id)
        self.servers = mycs.get_servers() 

        for s, v in zip(self.servers, vols) : 
            debug("attaching volume %s to server %s" % (v.name, s.name))
            v.attach_to_instance(s, mountpoint="/dev/xvdd")

        self.wait_for_storage_to_be_attached()

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        self.check()

        log("Building %d cloud servers" % self.cs_count)
        self.build_cs()

        log("Building and configuring lb ...")
        self.build_lb()

        log("Building and configuring dns domain ...")
        self.build_dns()

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
            Challenge11(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge11(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
