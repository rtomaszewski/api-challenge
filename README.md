# Rackspace API-chalange
==========

These are litle example scripts to demonstrate and show what can be done using Openstack cloud API.

More info can be found here:
* [Rackspace api-challenge summary] (http://rtomaszewski.blogspot.co.uk/2013/03/rackspace-api-challenge-summary.html)

## Part 1

* [API Challenges: By Support, for Support] (https://forums.rackspace.corp/discussion/268/api-challenges-by-support-for-support#Item_1)

Challenge 1: Write a script that builds three 512 MB Cloud Servers that following a similar naming convention. (ie., web1, web2, web3) and returns the IP and login credentials for each server. Use any image you want. Worth 1 point

Challenge 2: Write a script that clones a server (takes an image and deploys the image as a new server). Worth 2 Point

Challenge 3: Write a script that accepts a directory as an argument as well as a container name. The script should upload the contents of the specified directory to the container (or create it if it doesn't exist). The script should handle errors appropriately. (Check for invalid paths, etc.) Worth 2 Points

Challenge 4: Write a script that uses Cloud DNS to create a new A record when passed a FQDN and IP address as arguments. Worth 1 Point

## Part 2

Challenge 5: Write a script that creates a Cloud Database instance. This instance should contain at least one database, and the database should have at least one user that can connect to it. Worth 1 Point

Challenge 6: Write a script that creates a CDN-enabled container in Cloud Files. Worth 1 Point

Challenge 7: Write a script that will create 2 Cloud Servers and add them as nodes to a new Cloud Load Balancer. Worth 3 Points

Challenge 8: Write a script that will create a static webpage served out of Cloud Files. The script must create a new container, cdn enable it, enable it to serve an index file, create an index file object, upload the object to the container, and create a CNAME record pointing to the CDN URL of the container. Worth 3 Points
