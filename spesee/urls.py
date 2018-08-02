from django.conf.urls.defaults import *
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.contrib import admin
from mysite.nature.models import *
from mysite.nature.views import *

admin.autodiscover()

urlpatterns = [
	url(r'^admin/', include(admin.site.urls)),
	url(r'^', include('mysite.nature.urls')),
]