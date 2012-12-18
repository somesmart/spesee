from mysite.nature.models import UserSettings, ZipCode
from decimal import *
 
# ****************************************************************** #
# *********************** hide types view ************************** #
# ****************************************************************** #
def get_hide_list(user):
    hide_types = []
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