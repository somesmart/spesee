from django.shortcuts import get_object_or_404, render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.db.models import Q, Count
from django.views.generic import DetailView, ListView, UpdateView, CreateView, FormView
from django.contrib.auth import authenticate, login as auth_login
from django.core.urlresolvers import reverse
from django.template import RequestContext, loader, Context as TemplContext
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from haystack.query import SearchQuerySet, SQ
from tagging.models import Tag, TaggedItem
from mysite.nature.models import *
from mysite.nature.forms import *
from mysite.nature.utils import *
from decimal import *
from datetime import datetime
import csv

def thanks(request):
    return HttpResponse("<p>Thank you for your submission. It will be reviewed shortly.</p>")

class IndexListView(ListView):
    queryset=Organism.objects.select_related().annotate(observed=Count('observation__id')).order_by('-observation__observation_date')[:10]
    context_object_name='first_ogranisms'
    template_name='nature/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexListView, self).get_context_data(**kwargs)
        context['recent_updates'] = OrgIdentificationReview.objects.select_related().values('organism', 'organism__id', 'organism__common_name', 'organism__latin_name').annotate(updates=Count('id')).order_by('-moderated_date')[:10]
        return context

# ****************************************************************** #
# ********************* autocomplete views ************************* #
# ****************************************************************** #

def autocomplete(request):
    if request.method == "GET":
        if request.GET.has_key(u'term'):
            value = request.GET[u'term']
            search = request.GET[u'search']
            results = []
            if search == "organism":
                #this is only needed for by organism autocomplete because type doesn't impact zip.
                user = request.user
                hide_types = get_hide_list(user)
                # Ignore queries shorter than length 3
                if len(value) > 2:
                    model_results = Organism.objects.exclude(type__in=hide_types).filter(Q(common_name__icontains=value) | Q(latin_name__icontains=value))
                    # Default return list
                    for organism in model_results:
                        data = {'id': organism.id, 'label': organism.common_name + ' (' + organism.latin_name + ')'}
                        results.append(data)
                    json = simplejson.dumps(results)
                    return HttpResponse(json, mimetype='application/json')
                else:
                    return HttpResponseRedirect('/noresults/')
            elif search == "primary_search":
                #I may want to make this just a normal autocomplete to make it less resource intense in the future....
                if len(value) > 3:
                    model_results = SearchQuerySet().autocomplete(content_auto=value)
                    data = None
                    for organism in model_results:
                        try:
                            data = {'id': '/organism/' + str(organism.object.organism.id) + '/', 'label': organism.object.organism.common_name + ' (' + organism.object.organism.latin_name + ')'}
                        except:
                            data = {'id': '/organism/' + str(organism.object.id) + '/', 'label': organism.object.common_name + ' (' + organism.object.latin_name + ')' }                             
                        results.append(data)
                    json = simplejson.dumps(results)
                    return HttpResponse(json, mimetype='application/json')
                else:
                    return HttpResponseRedirect('/noresults/')
            elif search == "zip":
                # Ignore queries shorter than length 4
                if len(value) > 3:
                    model_results = ZipCode.objects.select_related().filter(zipcode__startswith=value)
                    for zipcode in model_results:
                        data = {'id': zipcode.id, 'label': zipcode.zipcode + ' - ' + zipcode.county}
                        results.append(data)
                    json = simplejson.dumps(results)
                    return HttpResponse(json, mimetype='application/json')
                else:
                    return HttpResponseRedirect('/noresults/')
            elif search == "user":
                # Ignore queries shorter than length 3
                if len(value) > 2:
                    model_results = UserSettings.objects.select_related().filter(user__username__startswith=value, private=False)
                    # Default return list
                    for user in model_results:
                        data = {'id': user.user.id, 'label': user.user.username}
                        results.append(data)
                    json = simplejson.dumps(results)
                    return HttpResponse(json, mimetype='application/json')
                else:
                    return HttpResponseRedirect('/noresults/')
        else:
            return HttpResponseRedirect('/noresults/')

def haystack_autocomplete(request):
    word = request.GET['q']
    limit = request.GET['limit']

    model_results = SearchQuerySet().autocomplete(content_auto=word)
    if limit:
        model_results = model_results[:int(limit)]

    results = []
    for organism in model_results:
        data = {'id': '/organism/' + str(organism.id) + '/', 'label': organism.common_name + ' (' + organism.latin_name + ')'}
        results.append(data)

    json = simplejson.dumps(results)
    return HttpResponse(json, mimetype='application/json')

# ****************************************************************** #
# *********************** the big map views ************************ #
# ****************************************************************** #

class MapView(ListView):
    #may want to return the template based on the map type, if that makes sense!
    template_name='nature/map_data.html'
    context_object_name='map_data'

    def get_queryset(self):
        self.maptype = self.kwargs['maptype']
        self.search_value = self.kwargs['pk']
        #only map by zip and location should exclude the hidden types. If you are on your list, a type list
        #or a specific organism list, you will want to see all values (otherwise why would you be there?)
        self.hide_types = get_hide_list(self.request.user)
        if self.maptype == 'type':
            return Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism__type = self.search_value)
        elif self.maptype == 'organism':
            return Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism = self.search_value)
        elif self.maptype == 'observation':
            return Observation.objects.select_related().filter(id = self.search_value)
        elif self.maptype == 'user':
            #this should not exclude children because we want all that user's results regardless if it's a child or not
            return Observation.objects.select_related().filter(user = self.search_value)
        elif self.maptype == 'list':
            #first selecting a list of organisms that are in the course, and then getting the map of those organisms
            #the template for this one should display different color markers if the user has seen it or not already
            self.org_ids = CourseDetail.objects.select_related().filter(course=self.search_value).values('organism')
            return Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism__in=self.org_ids)
        elif self.maptype == 'zip':
            #build out the horizontal and vertical box in which to search for observations
            self.zip_box = get_zip_box(self.search_value)
            return Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=self.hide_types).filter(latitude__range=(self.zip_box['zip_lat_left'], self.zip_box['zip_lat_right']), longitude__range=(self.zip_box['zip_lng_bottom'], self.zip_box['zip_lng_top']))
        elif self.maptype == 'location':
            self.location = Location.objects.get(id=self.search_value)
            self.add_width = (Decimal(str(.014)) * self.location.miles_wide)/2 #.014 is 1 mile times the width / 2 to cut it in half
            self.add_height = (Decimal(str(.014)) * self.location.miles_tall)/2
            self.lat_left = self.location.latitude - self.add_width
            self.lat_right = self.location.latitude + self.add_width
            self.lng_bottom = self.location.longitude - self.add_height
            self.lng_top = self.location.longitude + self.add_height
            return Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=self.hide_types).filter(latitude__range=(self.lat_left, self.lat_right), longitude__range=(self.lng_bottom, self.lng_top))

    def render_to_response(self, context, **kwargs):
        return super(MapView, self).render_to_response(context, content_type='application/xhtml+xml', **kwargs)         

# ****************************************************************** #
# ********************* organism related vws *********************** #
# ****************************************************************** #

def get_fields(self, request, *args, **kwargs):
        data = "<option value>---------</option>"
        if args[0]:
            data += "".join([
                "<option value='%(id)s'>%(name)s</option>" % x 
                for x in OrganismType.objects.get(pk=args[0]).id_fields.values()
            ])
        return HttpResponse(data)   

class OrganismView(DetailView):
    queryset=Organism.objects.select_related()
    template_name='nature/base_organism.html'

    def get_context_data(self, **kwargs):
        context = super(OrganismView, self).get_context_data(**kwargs)
        self.org_id = self.kwargs['pk']
        try:
            context['org_ident'] = OrgIdentification.objects.get(organism=self.org_id)
        except OrgIdentification.DoesNotExist:
            context['new_ident'] = {'org': self.org_id}
        context['map_observations'] = get_map_queryset('organism', self.org_id, self.request.user)
        return context

class OrganismViewTest(DetailView):
    queryset=Organism.objects.select_related()
    template_name='nature/base_organism_test.html'

    def get_context_data(self, **kwargs):
        context = super(OrganismViewTest, self).get_context_data(**kwargs)
        try:
            context['org_ident'] = OrgIdentification.objects.get(organism=self.kwargs['pk'])
        except OrgIdentification.DoesNotExist:
            context['new_ident'] = {'org': self.kwargs['pk']}
        return context        

def save_org_ident(request):
    org_id = request.POST[u'org']
    organism = Organism.objects.get(id=org_id)
    identification = request.POST[u'identification']
    modified_date = datetime.now()
    #if the user is a moderator their change is auto-approved
    if is_moderator(request.user):
        try:
            org_ident = OrgIdentification.objects.get(organism=organism)
        except OrgIdentification.DoesNotExist:
            org_ident = OrgIdentification(organism=organism, identification=identification)                        
        org_ident.identification=identification
        org_ident.save()
        #also want to save the review as approved for history purposes
        OrgIdentificationReview(organism=organism, identification=identification, modified_by=request.user, modified_date=modified_date, status=1).save()
        return HttpResponse('2') #this returns the "already approved" message
    else:
        OrgIdentificationReview(organism=organism, identification=identification, modified_by=request.user, modified_date=modified_date, status=2).save()
        return HttpResponse('1')

class TagListView(ListView):
    template_name='nature/base_search_tags.html'
    context_object_name='organism_list'

    def get_queryset(self):
        #get the orgtype id based on the org description (passed as the first variable in the url)
        self.orgtype = OrganismType.objects.get(description = self.kwargs['type'])
        self.tag = Tag.objects.get(name = self.kwargs['tag'])
        #get the organisms tagged with this tag and of the same org type
        return TaggedItem.objects.get_union_by_model(Organism.objects.filter(type=self.orgtype),self.tag)

class ImageUpload(CreateView):
    form_class = ImagesForm
    model = Images
    template_name = 'nature/base_head_image_upload.html'
    def form_valid(self, form):
        if form.is_valid():
            org_id = self.kwargs['pk']
            self.organism = Organism.objects.get(id=org_id)
            obj = form.save(commit=False) 
            obj.organism = self.organism
            obj.upload_user = self.request.user
            obj.upload_date = datetime.now()
            obj.status = 2
            obj.primary_image = False
            obj.save()
            new_image = Images.objects.get(id=obj.pk)
            ImagesReview(review_image=new_image, modified_by=obj.upload_user, modified_date=obj.upload_date, status=obj.status, primary_image=obj.primary_image).save()
            return HttpResponseRedirect('/thanks/')

def get_org_images(request, organism):
    images = Images.objects.filter(organism=organism, status=1) #only show approved images
    data = ""
    count = 1
    for x in images:
        if count == 1:
            data += "<div id='image' class='images'><img src='" + str(x.large_image.url) + "' border='0'></div>"
        data += "<a href='#' rel='" + str(x.large_image.url) + "' class='image'><img src='" + str(x.thumbnail.url) + "'class='thumb' border='0'/></a>"
        count += 1
    return HttpResponse(data)

# ****************************************************************** #
# ********************* tagging related vws ************************ #
# ****************************************************************** #

def organism_tags(request, organism):
    organism = Organism.objects.get(id=organism)
    tags = Tag.objects.get_for_object(organism)

    tag_list = []
    for tag in tags:
        data = {'id': tag.id, 'tag': tag.name}
        tag_list.append(data)

    results = {'tags': tag_list}
    json = simplejson.dumps(results)
    return HttpResponse(json, mimetype='application/json')

def type_tags(request, org_type):
    org_type = OrganismType.objects.get(id=org_type)
    tags = TypeTag.objects.select_related().filter(type=org_type)

    tag_list = []
    for tag in tags:
        data = {'id': tag.id, 'tag': tag.tag.name}
        tag_list.append(data)

    results = {'tags': tag_list}
    json = simplejson.dumps(results)
    return HttpResponse(json, mimetype='application/json')

def save_tags(request, organism):
    #add save tags code here
    organism = Organism.objects.get(id=organism)
    try:
        Tag.objects.update_tags(organism, request.POST[u'new_tags'])
        return HttpResponse('1')
    except:
        return HttpResponse('0')

# ****************************************************************** #
# ********************* organism review vws ************************ #
# ****************************************************************** #
class ReviewHome(ListView):
    template_name='nature/base_review.html'
    model = OrgIdentificationReview
    queryset = OrgIdentificationReview.objects.select_related().filter(status=2).aggregate(total_pending=Count('id'))
    context_object_name = 'organism_count'

    def get_context_data(self, **kwargs):
        context = super(ReviewHome, self).get_context_data(**kwargs)
        context['image_count'] = ImagesReview.objects.filter(status=2).aggregate(total_pending=Count('id'))
        context['obs_count'] = ObservationUnknown.objects.exclude(status=1).aggregate(total_pending=Count('id'))
        return context

class OrgIdentReviewList(ListView):
    template_name='nature/base_review_list.html'
    model = OrgIdentificationReview
    queryset = OrgIdentificationReview.objects.select_related().filter(status=2)
    context_object_name = 'org_review_list'

class OrgIdentReview(UpdateView):
    form_class = OrgIdentReviewForm
    model = OrgIdentificationReview
    template_name='nature/base_review_form.html'
    def form_valid(self, form):
        if form.is_valid():
            review = form.save(commit=False)
            review.moderated_by = self.request.user
            review.moderated_date = datetime.now()
            if review.status == 1:
                #update the primary identification table if the changes are approved
                try:
                    org_ident = OrgIdentification.objects.get(organism=review.organism)
                except OrgIdentification.DoesNotExist:
                    org_ident = OrgIdentification(organism=review.organism, identification=review.identification)                        
                org_ident.identification=review.identification
                org_ident.save()
            review.save()
            return HttpResponseRedirect('/review/organism/')

    def get_context_data(self, **kwargs):
        context = super(OrgIdentReview, self).get_context_data(**kwargs)
        self.pk = self.kwargs['pk']
        self.org_id = OrgIdentificationReview.objects.select_related().filter(id=self.pk).values('organism')
        try:
            context['current'] = OrgIdentification.objects.select_related().get(organism=self.org_id)
        except OrgIdentification.DoesNotExist:
            context['current']  = None
        context['new_values'] = OrgIdentificationReview.objects.select_related().get(id=self.pk)
        return context

class ObservationReviewList(ListView):
    template_name='nature/base_review_list.html'
    model = ObservationUnknown
    queryset = ObservationUnknown.objects.select_related().exclude(status=1)
    context_object_name = 'obs_review_list'

class ObservationReview(UpdateView):
    form_class = ObservationReviewForm
    model = ObservationUnknown
    template_name='nature/base_review_form.html'
    def form_valid(self, form):
        if form.is_valid():
            review = form.save(commit=False)
            review.moderated_by = self.request.user
            review.moderated_date = datetime.now()
            if review.status == 1:
                try:
                    review.organism = Organism.objects.get(id=form.data['organism'])
                    obs_unk = ObservationUnknown.objects.get(id=review.id)
                    Observation(organism=review.organism, user=obs_unk.user, observation_date=obs_unk.observation_date, temperature=obs_unk.temperature, latitude=obs_unk.latitude, longitude=obs_unk.longitude, location_descr=obs_unk.location_descr, comments=obs_unk.comments, quantity=obs_unk.quantity, observation_image=obs_unk.observation_image, parent_observation=obs_unk.parent_observation).save()
                except Organism.DoesNotExist:
                    review.organism = None                      
            review.save()
            return HttpResponseRedirect('/review/observation/')

    def get_context_data(self, **kwargs):
        context = super(ObservationReview, self).get_context_data(**kwargs)
        self.pk = self.kwargs['pk']
        context['new_values'] = ObservationUnknown.objects.select_related().get(id=self.pk)
        context['unknown_obs'] = {'new_obs': 1}
        return context

class ImagesReviewList(ListView):
    template_name='nature/base_review_list.html'
    model = ImagesReview
    queryset = ImagesReview.objects.select_related().filter(status=2)
    context_object_name = 'image_review_list'

class ImagesReviewUpdate(UpdateView):
    form_class = ImagesReviewForm
    model = ImagesReview
    template_name='nature/base_review_form.html'
    def form_valid(self, form):
        if form.is_valid():
            review = form.save(commit=False)
            review.moderated_by = self.request.user
            review.moderated_date = datetime.now()
            if review.status == 1:
                #update the primary identification table if the changes are approved
                try:
                    image = Images.objects.get(pk=review.review_image.id)
                except Images.DoesNotExist:
                    image = None                        
                image.status=review.status
                image.primary_image=review.primary_image
                image.save()
            review.save()
            return HttpResponseRedirect('/review/images/')

    def get_context_data(self, **kwargs):
        context = super(ImagesReviewUpdate, self).get_context_data(**kwargs)
        self.pk = self.kwargs['pk']
        try:
            context['new_values'] = ImagesReview.objects.select_related().get(id=self.pk)
            self.organism = context['new_values'].review_image.organism
        except ImagesReview.DoesNotExist:
            context['new_values'] = None
        context['new_image'] = {'new_image': 1}
        try:
            context['primary_image'] = Images.objects.select_related().get(organism=self.organism, primary_image=True)
        except Images.DoesNotExist:
            context['primary_image'] = None
        return context            

# ****************************************************************** #
# ********************* observation related ************************ #
# ****************************************************************** #

class ObservationCreateView(CreateView):
    form_class = ObservationForm
    def form_valid(self, form):
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = self.request.user
            if 'unknown' in self.request.POST:
                try:
                    obj.organism = Organism.objects.get(id=form.data['organism'])
                    ObservationUnknown(organism=obj.organism, user=obj.user, observation_date=form.cleaned_data['observation_date'], temperature=form.data['temperature'], latitude=form.data['latitude'], longitude=form.data['longitude'], location_descr=form.data['location_descr'], comments=form.data['comments'], quantity=form.data['quantity'], observation_image=form.data['observation_image'], modified_by=obj.user, modified_date=datetime.now(),status=3, reason='', moderated_by=None, moderated_date=datetime.now()).save()
                except:
                    ObservationUnknown(organism=None, user=obj.user, observation_date=form.cleaned_data['observation_date'], temperature=form.data['temperature'], latitude=form.data['latitude'], longitude=form.data['longitude'], location_descr=form.data['location_descr'], comments=form.data['comments'], quantity=form.data['quantity'], observation_image=form.data['observation_image'], modified_by=obj.user, modified_date=datetime.now(),status=3, reason='', moderated_by=None, moderated_date=datetime.now()).save()
            else:
                obj.organism = Organism.objects.get(id=form.data['organism'])
                if form.data['parent_observation'] == '':
                    obj.parent_observation = None #obj.id
                else:
                    obj.parent_observation = Observation.objects.get(id=form.data['parent_observation'])
                obj.save()
            return HttpResponseRedirect('/observation/')

    def get_context_data(self, **kwargs):
        context = super(ObservationCreateView, self).get_context_data(**kwargs)
        self.zipcode = UserSettings.objects.select_related().filter(user = self.request.user).values('zipcode')
        context['lat_lng'] = ZipCode.objects.get(id = self.zipcode)
        if self.request.GET.has_key(u'org'):
            self.org_id = self.request.GET[u'org']
            context['add_org'] = Organism.objects.get(id=self.org_id)
        return context

class ObservationUpdateView(UpdateView):
    form_class = ObservationForm
    model = Observation

    def get_context_data(self, **kwargs):
        context = super(ObservationUpdateView, self).get_context_data(**kwargs)
        self.zipcode = UserSettings.objects.select_related().filter(user = self.request.user).values('zipcode')
        context['lat_lng'] = ZipCode.objects.get(id = self.zipcode)
        return context

class ObservationList(ListView):
    template_name='nature/base_observation_list.html'
    context_object_name = 'observation_list'
    paginate_by = 30
    def get_queryset(self):
        self.search = self.kwargs['search']
        self.value = self.kwargs['pk']
        self.hide_types = get_hide_list(self.request.user)
        if self.search == 'user':
            return Observation.objects.select_related().exclude(organism__type__in=self.hide_types).filter(user = self.value).order_by('-observation_date')
        elif self.search == 'zip':
            self.zip_box = get_zip_box(self.value)
            return Observation.objects.select_related().exclude(organism__type__in=self.hide_types).exclude(parent_observation__isnull=False).filter(latitude__range=(self.zip_box['zip_lat_left'], self.zip_box['zip_lat_right']), longitude__range=(self.zip_box['zip_lng_bottom'], self.zip_box['zip_lng_top']))
        elif self.search == 'browse':
            return None
    def get_context_data(self, **kwargs):
        context = super(ObservationList, self).get_context_data(**kwargs)
        context['search_by'] = {'search_by': self.search, 'value': self.value}
        return context

class DiscoverList(ListView):
    template_name='nature/base_discover.html'
    context_object_name = 'discover_list'
    def get_queryset(self):
        self.search = self.kwargs['search']
        self.hide_types = get_hide_list(self.request.user)
        if self.request.method == "GET":
            if self.search == 'observation':
                try:
                    lat_lng_box = get_lat_lng_box(self.request.GET['latitude'], self.request.GET['longitude'], 100000) #100 is saying 100 feet * 100 feet
                except:
                    lat_lng_box = None
                if lat_lng_box:
                    return Observation.objects.select_related().filter(latitude__range=(lat_lng_box['lat_left'], lat_lng_box['lat_right']), longitude__range=(lat_lng_box['lng_bottom'], lat_lng_box['lng_top'])).exclude(parent_observation__isnull=False, organism__type__in=self.hide_types).order_by('organism__type')
            elif self.search == 'organism':
                try:
                    user_query = self.request.GET['q']
                    sqs = SearchQuerySet()
                    clean_query = sqs.query.clean(user_query)
                    sqs = sqs.filter(identification=clean_query)
                    return sqs
                except:
                    return None
        else:
            return None
    def get_context_data(self, **kwargs):
        context = super(DiscoverList, self).get_context_data(**kwargs)
        context['search_by'] = {'search_by': self.search}
        try:
            self.zipcode = UserSettings.objects.select_related().filter(user = self.request.user).values('zipcode')
        except:
            self.zipcode = UserSettings.objects.select_related().filter(user__id = 2).values('zipcode')
        context['lat_lng'] = ZipCode.objects.get(id = self.zipcode)
        return context

class ObservationListSelf(ListView):
    template_name='nature/base_observation_list.html'
    context_object_name = 'observation_list'
    paginate_by = 30
    def get_queryset(self):
        return Observation.objects.select_related().filter(user = self.request.user).order_by('-observation_date')
    def get_context_data(self, **kwargs):
        context = super(ObservationListSelf, self).get_context_data(**kwargs)
        context['search_by'] = {'search_by': 'user', 'value': self.request.user.id}
        context['unknown_obs'] = ObservationUnknown.objects.select_related().filter(user = self.request.user).order_by('-observation_date')
        return context

def check_existing(request, search_type, search_value):
    lat_lng_box = get_lat_lng_box(request.GET[u'lat'], request.GET[u'lng'], 100) #100 is saying 100 feet * 100 feet
    results=[]
    if search_type == 'existing':
        #only works for trees atm
        observations = Observation.objects.select_related().filter(organism__type=1,organism__id=search_value, latitude__range=(lat_lng_box['lat_left'], lat_lng_box['lat_right']), longitude__range=(lat_lng_box['lng_bottom'], lat_lng_box['lng_top'])).exclude(parent_observation__isnull=False)
        for obs in observations:
            if not obs.observation_image:
                data = {'obs_id': obs.id, 'location_descr': obs.location_descr, 'comments': obs.comments, 'image' : '' }#'lat_check': str(obs.latitude), 'lng_check': str(obs.longitude)}    
            else:
                data = {'obs_id': obs.id, 'location_descr': obs.location_descr, 'comments': obs.comments, 'image' : obs.observation_image.url }#'lat_check': str(obs.latitude), 'lng_check': str(obs.longitude)}
            results.append(data)
    json = simplejson.dumps(results)
    return HttpResponse(json, mimetype='application/json')

# ****************************************************************** #
# ********************* location related vws *********************** #
# ****************************************************************** #        

class LocationCreate(CreateView):
    form_class = LocationForm
    def form_valid(self, form):
        if form.is_valid():
            obj = form.save(commit=False)
            obj.created_by = self.request.user
            obj.save()
            return HttpResponseRedirect('/location/')

    def get_context_data(self, **kwargs):
        context = super(LocationCreate, self).get_context_data(**kwargs)
        self.zipcode = UserSettings.objects.select_related().filter(user = self.request.user).values('zipcode')
        context['lat_lng'] = ZipCode.objects.get(id = self.zipcode)
        return context

class LocationUpdate(UpdateView):
    form_class = LocationForm
    model = Location

class LocationList(ListView):
    template_name='nature/base_location_list.html'
    context_object_name = 'location_list'
    def get_queryset(self):
        if self.request.user.is_authenticated():
            return Location.objects.select_related().filter(created_by = self.request.user).order_by('description')
        else:
            return Location.objects.select_related().order_by('description')[:10]

    #need to set up a way to see other people's locations you want to see
    # def get_context_data(self, **kwargs):
    #     context = super(LocationList, self).get_context_data(**kwargs)
    #     context['subscribed_locations'] = Location.objects.get(id = self.zipcode)
    #     return context

class LocationView(DetailView):
    template_name='nature/base_location.html'
    queryset = Location.objects.select_related().order_by('description')

    def get_context_data(self, **kwargs):
        context = super(LocationView, self).get_context_data(**kwargs)
        self.search_value = self.kwargs['pk']
        self.hide_types = get_hide_list(self.request.user)
        self.location = Location.objects.get(id=self.search_value)
        self.add_width = ((Decimal(str(.014)) * self.location.miles_wide)/2) #.014 is 1 mile times the width / 2 to cut it in half
        self.add_height = ((Decimal(str(.014)) * self.location.miles_tall)/2)
        self.lat_left = self.location.latitude - self.add_width
        self.lat_right = self.location.latitude + self.add_width
        self.lng_bottom = self.location.longitude - self.add_height
        self.lng_top = self.location.longitude + self.add_height
        context['location_details'] = Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=self.hide_types).filter(latitude__range=(self.lat_left, self.lat_right), longitude__range=(self.lng_bottom, self.lng_top)).values('organism', 'organism__id', 'organism__common_name', 'organism__latin_name').annotate(Count('id')).order_by('organism__common_name')
        context['map_observations'] = Observation.objects.exclude(parent_observation__isnull=False).exclude(organism__type__in=self.hide_types).filter(latitude__range=(self.lat_left, self.lat_right), longitude__range=(self.lng_bottom, self.lng_top))
        return context

def delete_location(request, pk):
    location_user = Location.objects.select_related().get(id=pk)
    if request.user.id == location_user.created_by.id:
        Location.objects.filter(id=pk).delete()
        return HttpResponse("success")
    else:
        return HttpResponse("you shouldn't be here")

# ****************************************************************** #
# ********************* course related views *********************** #
# ****************************************************************** #

class CourseView(DetailView):
    template_name='nature/base_course.html'
    queryset = Course.objects.order_by('course_name')  

    def get_context_data(self, **kwargs):
        context = super(CourseView, self).get_context_data(**kwargs)
        self.course_id = self.kwargs['pk']
        self.course = Course.objects.get(id=self.course_id)
        #all the orgs in the list
        self.org_ids = CourseDetail.objects.select_related().filter(course=self.course_id).values('organism')
        #all the orgs in the list that have been seen
        self.observed_ids = Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism__in=self.org_ids).values('organism')
        #all the orgs that have been seen by the current user
        self.user_observed_ids = Observation.objects.filter(organism__in=self.org_ids, user=self.request.user).values('organism')
        #group memebers
        self.group_members = GroupUsers.objects.filter(group=self.course.group).values('user')
        self.group_finds = []
        if self.course.is_group:
            self.group_owner = Group.objects.filter(id=self.course.group.id).values('owner')
            self.group_finds = Observation.objects.filter(Q(organism__in=self.org_ids), Q(user__in=self.group_members) | Q(user=self.group_owner)).exclude(organism__in=self.user_observed_ids).values('organism')
        #all the orgs that OTHERS have seen, but not those the user has seen
        self.others_observed_ids = Observation.objects.filter(organism__in=self.org_ids).exclude(Q(organism__in=self.group_finds) | Q(organism__in=self.user_observed_ids)).values('organism')
        #distinct orgs from the course the current user has seen
        self.distinct_user_found = CourseDetail.objects.select_related().filter(organism__in=self.user_observed_ids, course=self.course_id).order_by('organism__common_name')
        #amount found by the user
        self.total_found_user = len(self.distinct_user_found)
        #count of the course
        self.course_total = len(self.org_ids)
        #pull the orgs in the list that have been seen by the user
        context['user_found'] = self.distinct_user_found
        #items from course found by group
        context['group_found'] = CourseDetail.objects.select_related().filter(organism__in=self.group_finds, course=self.course_id).order_by('organism__common_name').distinct()        
        #those found by other users
        context['others_found'] = CourseDetail.objects.select_related().filter(organism__in=self.others_observed_ids, course=self.course_id).order_by('organism__common_name').distinct()
        #those orgs not ever found
        context['never_found'] = CourseDetail.objects.select_related().filter(course=self.course_id).exclude(organism__in=self.observed_ids).distinct().order_by('organism__common_name').distinct()
        #percent complete stats
        getcontext().prec = 2
        context['completion'] = {'total': self.course_total, 'total_user': self.total_found_user}
        context['map_observations'] = get_map_queryset('list', self.course_id, self.request.user)
        return context

class CourseList(ListView):
    template_name='nature/base_course_list.html'
    context_object_name = 'course_list'
    def get_queryset(self):
        return Course.objects.filter(user = self.request.user)    

    def get_context_data(self, **kwargs):
        context = super(CourseList, self).get_context_data(**kwargs)
        self.groups = GroupUsers.objects.select_related().filter(user=self.request.user, status=1).values('group').distinct()
        context['member_of'] = Course.objects.filter(group__in=self.groups)
        return context

class CourseCreateView(CreateView):
    template_name = 'nature/base_course_create.html'
    model = Course #Must keep this
    form_class = CourseForm

    def form_valid (self, form):
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = self.request.user
            if obj.is_group:
                obj.group = Group.objects.get(id=form.data['group'])
            obj.save()
        #add the option here to define a group if "is_group == True"    
        context = self.get_context_data()
        coursedetail_form = context['coursedetail_form']
        if coursedetail_form.is_valid():
            self.object = form.save()
            coursedetail_form.instance = self.object
            coursedetail_form.save()
            return HttpResponseRedirect('/list/')
        else:
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_context_data(self, **kwargs):
        context = super(CourseCreateView, self).get_context_data(**kwargs)
        if self.request.POST:
            context['coursedetail_form'] = CourseDetailFormSet(self.request.POST, instance=self.object)
            # context['courseusers_form'] = CourseUserForm(self.request.POST, instance=self.object)
        else:
            context['coursedetail_form'] = CourseDetailFormSet(instance=self.object)
            # context['courseusers_form'] = CourseUserForm(instance=self.object)
        context['group_list'] = Group.objects.filter(owner=self.request.user)
        return context

def delete_list(request, pk):
    course_user = Course.objects.select_related().get(id=pk)
    if request.user.id == course_user.user.id:
        Course.objects.filter(id=pk).delete()
        return HttpResponse("success")
    else:
        return HttpResponse("you shouldn't be here")

class CourseUpdate(UpdateView):
    template_name = 'nature/base_course_update.html'
    model = Course #Must keep this
    form_class = CourseForm

    def form_valid (self, form):
        if form.is_valid():
            obj = form.save(commit=False)
            obj.group = Group.objects.get(id=form.data['group'])
            obj.save()
            return HttpResponseRedirect('/list/')

    def get_context_data(self, **kwargs):
        context = super(CourseUpdate, self).get_context_data(**kwargs)
        self.course_id = self.kwargs['pk']
        context['detail_list'] = CourseDetail.objects.select_related().filter(course=self.course_id).order_by('organism__common_name')  
        context['group_list'] = Group.objects.filter(owner=self.request.user)
        return context        

def delete_list_item(request, pk):
    course_user = Course.objects.select_related().get(course_details__id=pk)
    if request.user.id == course_user.user.id:
        CourseDetail.objects.filter(id=pk).delete()
        return HttpResponse("success")
    else:
        return HttpResponse("you shouldn't be here")

def add_list_item(request, course, organism):
    course_user = Course.objects.select_related().get(id=course)
    organism = Organism.objects.get(id=organism)
    if request.user.id == course_user.user.id:
        new_item = CourseDetail(course=course_user, organism=organism)
        new_item.save()
        return HttpResponse(new_item.id)
    else:
        return HttpResponse("you shouldn't be here")

# ****************************************************************** #
# ********************* groups related views *********************** #
# ****************************************************************** #

class GroupView(DetailView):
    template_name='nature/base_group.html'
    queryset = Group.objects.order_by('name')  

    def get_context_data(self, **kwargs):
        context = super(GroupView, self).get_context_data(**kwargs)
        self.group_id = self.kwargs['pk']
        context['detail_list'] = GroupUsers.objects.select_related().filter(group=self.group_id).order_by('user__username')  
        context['group_lists'] = Course.objects.filter(group = self.kwargs['pk'])
        return context    

class GroupList(ListView):
    template_name='nature/base_group_list.html'
    context_object_name = 'group_list'
    def get_queryset(self):
        return Group.objects.select_related().filter(owner = self.request.user)  
    def get_context_data(self, **kwargs):
        context = super(GroupList, self).get_context_data(**kwargs)  
        context['joined_groups'] = Group.objects.select_related().filter(group_users__user = self.request.user)
        return context

class GroupCreateView(CreateView):
    template_name = 'nature/base_group_create.html'
    model = Group #Must keep this
    form_class = GroupForm

    def form_valid (self, form):
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = self.request.user
            obj.save()
            return HttpResponseRedirect('/edit/group/' + str(obj.id) + '/')

def delete_group(request, pk):
    group_owner = Group.objects.select_related().get(id=pk)
    if request.user.id == group_owner.owner.id:
        Group.objects.filter(id=pk).delete()
        return HttpResponse("success")
    else:
        return HttpResponse("you shouldn't be here")

class GroupUpdate(UpdateView):
    template_name = 'nature/base_group_update_head.html'
    model = Group #Must keep this
    form_class = GroupForm

    def get_success_url(self, **kwargs):
        return '/edit/group/' + self.kwargs['pk'] + '/'

    def get_context_data(self, **kwargs):
        context = super(GroupUpdate, self).get_context_data(**kwargs)
        self.group_id = self.kwargs['pk']
        context['detail_list'] = GroupUsers.objects.select_related().filter(group=self.group_id).order_by('user__username')  
        return context        

def delete_group_user(request, pk):
    group_owner = Group.objects.select_related().get(group_users__id=pk)
    if request.user.id == group_owner.owner.id:
        GroupUsers.objects.filter(id=pk).delete()
        return HttpResponse("success")
    else:
        return HttpResponse("you shouldn't be here")

def add_group_user(request, group, user, status):
    group_id = Group.objects.select_related().get(id=group)
    user = User.objects.get(id=user)
    if request.user.id == group_id.owner.id:
        new_user = GroupUsers(group=group_id, user=user, status=status)
        new_user.save()
        return HttpResponse(new_user.id)
    elif not group_id.private:
        new_user = GroupUsers(group=group_id, user=user, status=status)
        new_user.save()
        return HttpResponse(new_user.id)
    else:
        return HttpResponse("you shouldn't be here")

def group_invite_response(request, group, response):
    try:
        group_user = GroupUsers.objects.get(group=group, user=request.user)
    except GroupUsers.DoesNotExist:
        group_user = None
    if group_user:
        group_user.status = response
        group_user.save()
        return HttpResponse("success")
    else:
        return HttpResponse("you shouldn't be here")

def get_user_groups(request, user):
    groups = Group.objects.filter(owner=user)
    data = "<option value>---------</option>"
    for x in groups:
        data += "<option value='" + str(x.id) + "'>" + x.name + "</option>"
    return HttpResponse(data)        

# ****************************************************************** #
# ********************* search related views *********************** #
# ****************************************************************** #
def get_ident_fields(request, type_name):
    ident_fields = IdentificationField.objects.select_related().filter(type__description=type_name).order_by('name')
    data = "<option value>---------</option>"
    for x in ident_fields:
        data += "<option value='" + x.name + "'>" + x.name + "</option>"
    return HttpResponse(data)

def get_ident_details(request, type_name, id_field):
    field_set = IdentificationField.objects.select_related().filter(type__description=type_name, name=id_field).distinct()
    ident_details = IdentificationDetail.objects.filter(field=field_set).values('description').order_by('description').distinct()
    data = "<option value>---------</option>"
    for x in ident_details:
        data += "<option value='" + x['description'] + "'>" + x['description'] + "</option>"
    return HttpResponse(data)

# ****************************************************************** #
# ********************* user signup edit etc *********************** #
# ****************************************************************** #

class UserInvitesView(ListView):
    context_object_name = "group_invites"
    def get_queryset(self):
        return GroupUsers.objects.select_related().filter(user=self.request.user, status=2)

class UserSettingsView(UpdateView):
    form_class = UserSettingsForm
    model = UserSettings
    def get_queryset(self):
        return UserSettings.objects.filter(user = self.kwargs['pk'])
    def form_valid(self, form):
        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = self.request.user
            obj.zipcode = ZipCode.objects.get(id=form.data['zipcode'])
            try:
                obj.private = form.data['private']
            except:
                obj.private = False
            obj.save()
            return HttpResponseRedirect('/accounts/profile/' + str(self.request.user.username) + '/')        

class UserDetailView(DetailView):
    template_name='nature/base_profile.html'
    def get_queryset(self):
        return UserSettings.objects.filter(user = self.kwargs['pk'])

#this works, but the editing by username doesn't so I will leave both in there
def user_profile(request, username):
    context_dict = {}
    user = get_object_or_404(User, username=username)
    profile = get_object_or_404(UserSettings, user=user)

    context_dict = { 'usersettings': profile, }
    return render_to_response('nature/base_profile.html', context_dict, RequestContext(request))        

def get_invite_list(request, user):
    invites = GroupUsers.objects.select_related().filter(user=user, status=2).values('group__name', 'group__id', 'user__id')
    invites = list(invites)
    json = simplejson.dumps(invites)
    return HttpResponse(json, mimetype='application/json')

def get_invite_count(request, user):
    invites = GroupUsers.objects.filter(user=user, status=2).aggregate(total_invites=Count('id'))
    json = simplejson.dumps(invites)
    return HttpResponse(json, mimetype='application/json')

def login(request):
    if 'username' in request.POST:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth_login(request, user)
                return HttpResponse('1')
            else:
                return HttpResponse('0') #disabled account
        else:
            return HttpResponse('2') #invalid login
    else:
        return HttpResponseRedirect('/noresults/')

# ****************************************************************** #
# ********************* global/user stats vw *********************** #
# ****************************************************************** #

class StatsView(ListView):
    queryset = Course.objects.aggregate(Count('id'))
    context_object_name = 'stats_list'

    def get_context_data(self, **kwargs):
        context = super(StatsView, self).get_context_data(**kwargs)
        context['orgs_found'] = Observation.objects.exclude(parent_observation__isnull=False).aggregate(total_found=Count('organism'))
        return context

# ****************************************************************** #
# *********************** export data views ************************ #
# ****************************************************************** #

def export_obs(request):
    # Create the HttpResponse object with the appropriate CSV header.
    response = HttpResponse(mimetype='text/csv')
    response['Content-Disposition'] = 'attachment;filename="observations.txt"'

    observations = Observation.objects.select_related().filter(user=request.user)

    t = loader.get_template('nature/observation_export.txt')
    c = TemplContext({
        'observations': observations,
    })
    response.write(t.render(c))
    return response
