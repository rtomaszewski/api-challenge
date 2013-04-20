import os
import sys
import json
import re
import time
import datetime, time

from pprint import pprint
from pprint import pformat

from novaclient.v1_1 import client

os.environ["OS_USERNAME"]
os.environ["OS_PASSWORD"]
os.environ["OS_NO_CACHE"]
os.environ["OS_TENANT_NAME"]
os.environ["OS_AUTH_URL"]
os.environ["OS_REGION_NAME"]
os.environ["OS_AUTH_SYSTEM"]
os.environ["NOVA_RAX_AUTH"]
os.environ["OS_PROJECT_ID"]

from novaclient import auth_plugin as _cs_auth_plugin
_cs_auth_plugin.discover_auth_systems()
auth_plugin = _cs_auth_plugin.load_plugin("rackspace_uk")

cs = client.Client(os.environ["OS_USERNAME"], os.environ["OS_PASSWORD"], os.environ["OS_TENANT_NAME"], auth_url=os.environ["OS_AUTH_URL"], auth_system="rackspace", region_name="LON",  service_type="compute", auth_plugin=auth_plugin)

help_str="""
the novaclient module has been loaded and INITIATED, try typing one of the commands below to see if it works.

#example 1: whow all cloud servers under you cloud account 
l=cs.servers.list()
print(l)

# example 2: show list of images 
pprint(cs.images.list())
"""

print(help_str)

