import os
import sys
import json
import re
import time
import datetime, time

from pprint import pprint
from pprint import pformat

import pyrax

creds_file = os.path.expanduser("~/rackspace_cloud_credentials")
pyrax.set_credential_file(creds_file, "LON")
cs = pyrax.cloudservers

help_str="""
the pyrax module has been loaded, try typing one of the commands below to see if it works.

#example 1: whow all cloud servers under you cloud account 
l=cs.servers.list()
print(l)

# example 2: show list of images 
pprint(cs.images.list())
"""

print(help_str)

