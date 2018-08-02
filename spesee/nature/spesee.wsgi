import os
import sys

path='/home/somesmart'

if path not in sys.path:
  sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'spesee_settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
