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
from base import log, debug

DEBUG = 0

PROGRAM_NAME = "challenge5.py" 

class Challenge5(ChallengeBase): 
    """ 
    Challenge 5: Write a script that creates a Cloud Database instance. This instance should contain at least one 
    database, and the database should have at least one user that can connect to it.
    """

    def __init__ (self, debug_level=0, args=[], optlist=[]) :
        ChallengeBase.__init__(self, debug_level)

        self.message ="""
    usage: %s [-h] [-v] [ -i | -d ] [ -u db-user ] [ instance-name ] [ db-name1 [db-name2] ] 
        -h - usage help 
        -v - verbose / debug output 
        -i - if instance exists delete it and all its databases before proceeding 
        -d - delete database(s) from under the instance

        instance-name - create instance with this name 
        db-nameX - name of the database
        db-user - create user that can access the database; by default a user name is equal to db-name
    """ % (PROGRAM_NAME)

        self.optlist = optlist
        self.args = args

        self.db_users=None
        self.dbs=[]

        self.db_instance_name=None
        self.db_instance = None
        
        
        self.opt_delete_instance = False
        self.opt_delete_db = False

        for o, val in optlist:
            if o == "-i":
                self.opt_delete_instance=True
            elif o == "-d":
                self.opt_delete_db=True
            elif o == "-u":
                self.db_users=[ val ]

        try:
            self.db_instance_name = self.args[0]
            self.dbs = self.args[1:]

        except Exception, e:
            pass

        debug("instance %s dbs %s users %s" % (self.db_instance_name, self.dbs, self.db_users))

    def check_str(self, s):
        # http://docs.rackspace.com/cdb/api/v1.0/cdb-devguide/content/user_management.html
        return bool(re.match('^[a-z0-9-_]+$', s, re.IGNORECASE))

    def check(self):
        debug("check start")
        ret = True

        if self.db_instance_name is None:
            self.db_instance_name = "challenge5-inst1"
        
        elif self.check_str(self.db_instance_name) == False:
            log("instance name `%s` incorrect, please use only alphanumeric and `-_.` chars" % self.db_instance_name)
            ret=False
        
        # http://docs.rackspace.com/cdb/api/v1.0/cdb-devguide/content/POST_createInstance__version___accountId__instances_.html
        if len(self.db_instance_name) > 255 :
            log("instance name `%s` is too long (max 255 chars) " % self.db_instance_name)
            ret=False

        if ret : 
            ret=self.delete_db_instance(self.db_instance_name)

        if self.dbs :
            for db in self.dbs :
                if self.check_str(db) == False:
                    log("db name `%s` incorrect, please use only alphanumeric and `-_.` chars" % db)
                    ret=False
        else: 
            self.dbs = [ "challenge5-db1", "challenge5-db2" ]

        # http://docs.rackspace.com/cdb/api/v1.0/cdb-devguide/content/POST_createDatabase__version___accountId__instances__instanceId__databases_.html
        for db in self.dbs :
            if len(db) > 64 :
                log("db name `%s` is too long (max 64 chars) " % db )
                ret=False

        if self.db_users :
            for user in self.db_users :
                if self.check_str(user) == False:
                    log("user name `%s` incorrect, please use only alphanumeric and `-_.` chars" % user)
                    ret=False
        else: 
            self.db_users = [ "challenge5-user1", "challenge5-user2" ] 

        # http://docs.rackspace.com/cdb/api/v1.0/cdb-devguide/content/POST_createUser__version___accountId__instances__instanceId__users_.html
        for u in self.db_users :
            if len(u) > 16 :
                log("user name `%s` is too long (max 16 chars) " % u)
                ret=False

        debug("instance %s dbs %s users %s" % (self.db_instance_name, self.dbs, self.db_users))
        return ret

    def delete_db_instance(self, db_instance_name):
        debug("delete_db_instance start")

        try:
            db=self.cdb.find( name=db_instance_name )

            if self.opt_delete_instance :
                log("Found existing db instance %s, deleting it ..." % db_instance_name)
                db.delete()
                time.sleep(5) #ugly hack
            else :
                log("db instace exists; remove it or provide other instance name, canceling ...")
                return False

        except exc.NotFound, e:
            debug("no instace %s found" % db_instance_name)

        return True

    def create_db_instance(self, db_instance_name) :
        debug("create_db_instance start")
        flavor=1
        volume=1

        self.db_instance = self.cdb.create(db_instance_name, flavor=flavor, volume=volume)

    def check_db_instance(self, db_instance_name):
        """ returns True when the instance is built otherwise False """
        debug("check_db_instance start")

        inst=self.cdb.find( name=db_instance_name)
        return inst.status == "ACTIVE"

    def wait_for_instance_build(self):
        debug("wait_for_instance_build start")

        wait = WaitingForTask(self.check_db_instance, [self.db_instance_name])
        if wait.wait_for_tasks() == False: 
            self.db_instance.delete()
            sys.exit()

    def create_dbs(self):
        debug("create_dbs start")

        for db in self.dbs : 
            log("creating db: %s" % db)
            self.db_instance.create_database(db)

    def create_users(self):
        debug("create_users start")
        password="pass123@"

        for user in self.db_users : 
            self.db_instance.create_user(user, password, self.dbs)  
            log("Created user %s pass %s in db %s" % (user, password, self.dbs) )

    def show(self):
        debug("show start")

    def run(self):
        debug("run start")
        ChallengeBase.run(self)
        
        if self.check() is False:
            self.usage()
            sys.exit(-1)

        log("Creating instance %s" % self.db_instance_name)
        self.create_db_instance(self.db_instance_name)

        log("Waiting for the instance to be built ...")
        self.wait_for_instance_build()
        log("Instance is created on host %s" % self.db_instance.hostname)

        log("Creating databases %s under the instance %s" % (self.dbs, self.db_instance_name) )
        self.create_dbs()

        log("Creating users %s" % (self.db_users) )
        self.create_users()

if __name__ == '__main__': 
    optlist, args = getopt.getopt(sys.argv[1:], 'vhid')

    for o, val in optlist:
        if o == "-v":
            DEBUG = 1
            base.DEBUG = 1

            debug("options: " + ', '.join( map(str,optlist) ) ) 
            debug("arguments: " + ", ".join(args) )

        elif o == "-h":
            Challenge5(debug_level=DEBUG).usage()
            sys.exit()

    challenge = Challenge5(debug_level=DEBUG, args=args, optlist=optlist)
    challenge.run()
