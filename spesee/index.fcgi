#!/usr/bin/python
import sys, os

sys.path.insert(0, "/home/mission")
sys.path.insert(0, "/home/mission/lib/python2.6/site-packages/")

# Switch to the directory of your project.
os.chdir("/home/mission/mysite")

# Set the DJANGO_SETTINGS_MODULE environment variable.
os.environ['DJANGO_SETTINGS_MODULE'] = "mysite.settings"

from django.core.servers.fastcgi import runfastcgi
runfastcgi(method="threaded", daemonize="false")
