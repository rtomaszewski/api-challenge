import re
# cs.networks
# {u'private': [u'10.178.197.30'],
#  u'public': [u'95.138.180.58', u'2a00:1a48:7805:0111:8cfc:cf10:ff08:4465']}

def get_ipv4net(net_list):
    if type(net_list) is not  list :
        net_list = [net_list]

    for net in net_list:
        if '.' in net : 
            return net

    return None

def get_image(cs):
    [ image ] = filter ( lambda x : bool(re.match("Ubuntu 10.04.*" , x.name)), cs.images.list())
    return image.id

def get_flavor(cs):
    [ f512 ] = filter( lambda x : x.ram==512 , cs.flavors.list())
    return f512.id