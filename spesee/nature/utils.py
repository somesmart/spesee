from nature.models import UserSettings, ZipCode, Observation, CourseDetail
from django.db.models import Q
from decimal import *
 
# ****************************************************************** #
# *********************** hide types view ************************** #
# ****************************************************************** #
def get_hide_list(user):
    hide_types = [0] #sets it to hide nothing by default for anonymous users
    if user.is_authenticated():
        user_hides = UserSettings.objects.get(user = user)
        if user_hides.hide_trees == True:
            hide_types.append(1)
        if user_hides.hide_birds == True:
            hide_types.append(2)
        if user_hides.hide_mammals == True:
            hide_types.append(3)
        if user_hides.hide_amphibians == True:
            hide_types.append(4)
        if user_hides.hide_reptiles == True:
            hide_types.append(5)
    return hide_types

def get_zip_box(zipcode):
    data = ZipCode.objects.get(zipcode = zipcode)    
    zip_lat = data.latitude
    zip_lng = data.longitude
    add_value = Decimal(str(.07)) #this is about 5 miles
    zip_lat_left = zip_lat - add_value
    zip_lat_right = zip_lat + add_value
    zip_lng_bottom = zip_lng - add_value
    zip_lng_top = zip_lng + add_value    
    zip_box = {'zip_lat_left': zip_lat_left, 'zip_lat_right': zip_lat_right, 'zip_lng_bottom': zip_lng_bottom, 'zip_lng_top': zip_lng_top}
    return zip_box

def get_lat_lng_box(lat, lng, size):
    add_value = Decimal(str(.0000028*size)) #this makes a box about size * feet
    lat = Decimal(str(lat))
    lng = Decimal(str(lng))
    lat_left = lat - add_value
    lat_right = lat + add_value
    lng_top = lng + add_value
    lng_bottom = lng - add_value
    lat_lng_box = {'lat_left': lat_left, 'lat_right': lat_right, 'lng_bottom': lng_bottom, 'lng_top': lng_top}
    return lat_lng_box

def is_moderator(user):
    if user:
        return user.groups.filter(name='Moderator').exists()
    return False

def get_map_queryset(maptype, search_value, user):
    #only map by zip and location should exclude the hidden types. If you are on your list, a type list
    #or a specific organism list, you will want to see all values (otherwise why would you be there?)
    hide_types = get_hide_list(user)
    private_obs = []
    public_obs = []
    if maptype == 'type':
        public_obs = Observation.objects.select_related().exclude(Q(private=True) | Q(parent_observation__isnull=False)).filter(organism__type = search_value)
        private_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism__type = search_value, user = user, private=True)
    elif maptype == 'organism':
        public_obs = Observation.objects.select_related().exclude(Q(private=True) | Q(parent_observation__isnull=False)).filter(organism = search_value)
        private_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism = search_value, user = user, private=True)
    elif maptype == 'observation':
        public_obs = Observation.objects.select_related().filter(id = search_value, private=False)
        private_obs = Observation.objects.select_related().filter(id = search_value, private=True, user=user)
    elif maptype == 'user':
        #this should not exclude children because we want all that user's results regardless if it's a child or not
        private_obs = Observation.objects.select_related().filter(user = search_value)
    elif maptype == 'list':
        #first selecting a list of organisms that are in the course, and then getting the map of those organisms
        #the template for this one should display different color markers if the user has seen it or not already
        org_ids = CourseDetail.objects.select_related().filter(course=search_value).values('organism')
        public_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism__in=org_ids, private=False)
        private_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).filter(organism__in=org_ids, private=True, user = user)
    elif maptype == 'zip':
        #build out the horizontal and vertical box in which to search for observations
        zip_box = get_zip_box(search_value)
        public_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=hide_types).filter(latitude__range=(zip_box['zip_lat_left'], zip_box['zip_lat_right']), longitude__range=(zip_box['zip_lng_bottom'], zip_box['zip_lng_top']), private=False)
        private_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=hide_types).filter(latitude__range=(zip_box['zip_lat_left'], zip_box['zip_lat_right']), longitude__range=(zip_box['zip_lng_bottom'], zip_box['zip_lng_top']), private=True, user=user)
    elif maptype == 'location':
        location = Location.objects.get(id=search_value)
        add_width = (Decimal(str(.014)) * location.miles_wide)/2 #.014 is 1 mile times the width / 2 to cut it in half
        add_height = (Decimal(str(.014)) * location.miles_tall)/2
        lat_left = location.latitude - add_width
        lat_right = location.latitude + add_width
        lng_bottom = location.longitude - add_height
        lng_top = location.longitude + add_height
        public_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=hide_types).filter(latitude__range=(lat_left, lat_right), longitude__range=(lng_bottom, lng_top), private=False)
        private_obs = Observation.objects.select_related().exclude(parent_observation__isnull=False).exclude(organism__type__in=hide_types).filter(latitude__range=(lat_left, lat_right), longitude__range=(lng_bottom, lng_top), private=True, user=user)
    map_queryset = public_obs | private_obs
    return map_queryset