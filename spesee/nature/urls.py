from django.conf.urls import *
from django.urls import include, re_path
from django.contrib.auth.decorators import login_required
from django.views.generic import *
from django.db.models import Count
from django.contrib import admin
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from nature.models import *
from nature import views as nature_views
from nature.signals import *
from nature.forms import *
# from registration.backends.default.views import RegistrationView
import nature.signals

admin.autodiscover()

urlpatterns = [
    re_path(r'^djangojs/', include('djangojs.urls')),
    #home page
    re_path(r'^$', nature_views.IndexListView.as_view(), name='home-page'),
    re_path(r'^$', nature_views.IndexListView.as_view(), name='my-books'),
    #about page
    re_path(r'^about/$', TemplateView.as_view(template_name = 'nature/base_about.html'), name='about-page'),
    #organism type details
    re_path(r'^type/(?P<pk>\d+)/',DetailView.as_view(model=OrganismType, template_name='nature/type.html'), name='type-view'),
    #list of types
    re_path(r'^type/', ListView.as_view(model=OrganismType, context_object_name='type_list', template_name='nature/base_type.html')),
    #org tag types
    re_path(r'^tags/type/(?P<org_type>\d+)/$', nature_views.type_tags, name='nature-type-tags'),
    #organism tagging
    re_path(r'^tags/organism/(?P<organism>\d+)/$', nature_views.organism_tags, name='organism-tags'),
    #search tags
    re_path(r'^tags/search/(?P<type>[\w]+)/(?P<tag>[\s\w]+)/$',nature_views.TagListView.as_view(), name='nature-search-tags'),
    #save tags
    re_path(r'^save/tags/organism/(?P<organism>\d+)/$', nature_views.save_tags, name='nature-save-tags'),
    #save org ident
    re_path(r'^save/organism/ident/', nature_views.save_org_ident, name='save-org-ident'),
    #/organism/
    re_path(r'^organism/(?P<pk>\d+)/', nature_views.OrganismView.as_view(), name='organism-view'),
    re_path(r'^test/organism/(?P<pk>\d+)/', nature_views.OrganismViewTest.as_view(), name='organism-view-test'),
    #/check for existing obs for that org/lat/lng
    re_path(r'^check/(?P<search_type>\w+)/(?P<search_value>\d+)/', nature_views.check_existing, name='check-existing'),
    re_path(r'^review/$', nature_views.ReviewHome.as_view(), name='nature-review-home'),
    #list organism changes to be reviewed
    re_path(r'^review/organism/$', nature_views.OrgIdentReviewList.as_view(), name='review-organism-list'),
    #specific item to be reviewed
    re_path(r'^review/organism/(?P<pk>\d+)/$', nature_views.OrgIdentReview.as_view(), name='review-organism-view'),
    #obs to be reviewed
    re_path(r'^review/observation/$', nature_views.ObservationReviewList.as_view(), name='review-obs-list'),
    #specific obs to be reviewed
    re_path(r'^review/observation/(?P<pk>\d+)/$', nature_views.ObservationReview.as_view(), name='review-obs'),
    #list of images to be reviewed
    re_path(r'^review/images/$', nature_views.ImagesReviewList.as_view(), name='review-image-list'),
    #specific image to be reviewed
    re_path(r'^review/images/(?P<pk>\d+)/$', nature_views.ImagesReviewUpdate.as_view(), name='review-image'),
    #upload an image
    re_path(r'^organism/image/upload/(?P<pk>\d+)/$', nature_views.ImageUpload.as_view(), name='image-upload'),
    #get images for an organism to add to the ident details
    re_path(r'^organism/image/(?P<organism>\d+)/$', nature_views.get_org_images, name='image-list'),
    #build a search page
    #this section is currently commented out to avoid interfering with haystack. I may keep these features, but I need to move them.
    #re_path(r'^search/$', ListView.as_view(
    #        model=OrganismType,
    #        context_object_name='type_list',
    #        template_name='nature/base_search.html')),
    #get the id_fields from the selected type
    #re_path(r'^search/(?P<type_name>\w+)/$', nature_views.get_ident_fields', name='type_search'),
    #get the id_detail values from the id_field/type selected
    #re_path(r'^search/(?P<type_name>\w+)/(?P<id_field>[\s\w]+)/$', nature_views.get_ident_details', name='id_field_search'),
    #ident/is for ident fields (shows organisms with a certain value in an particular ident field)
    #so, for example you might want to find Birds(type) with a color(ident field) of White (details)
    # re_path(r'^ident/(\w+)/([\s\w]+)/([\s\w]+)/$',    
    #     IdentDetailListView.as_view(), name='search-ident'),
    #haystack search urls
    re_path(r'^search/', include('haystack.urls')),
    #observations by user, zip, etc
    re_path(r'^observation/(?P<search>\w+)/(?P<pk>\d+)/$', login_required(nature_views.ObservationList.as_view()), name='observation-list'),
    #observation/$ shows all observations for the user logged in
    re_path(r'^observation/$', login_required(nature_views.ObservationListSelf.as_view()), name="observation-home"),
    #observation/(?<pk>\d+) displays a specific observation
    re_path(r'^observation/(?P<pk>\d+)/$', DetailView.as_view(queryset = Observation.objects.select_related(), context_object_name='observation', template_name='nature/base_observation.html'), name='observation-detail'),
    #edit/observation/(?<pk>\d+)/ is for a user to edit their own observation
    re_path(r'^edit/observation/(?P<pk>\d+)/$', login_required(nature_views.ObservationUpdateView.as_view(template_name='nature/base_observation_form.html')), name='edit-observation'),
    #add/observation/ is to add an observation
    re_path(r'^add/observation/$', login_required(nature_views.ObservationCreateView.as_view(template_name='nature/base_observation_form.html')), name='add-observation'),
    #export my observations
    re_path(r'observation/export/$', nature_views.export_obs, name='export-observations'),
    #shows the login screen
    re_path(r'^accounts/login/$', auth_views.LoginView, {'template_name': 'nature/base_login.html'}, name='account-login'),
    re_path(r'^accounts/login/simple/$', nature_views.login, name='login-simple'),
    #logout the user
    re_path(r'^accounts/logout/$', auth_views.LogoutView, {'template_name': 'nature/base_logged_out.html'}, name='account-logout'),
    #shows the user profile page
    re_path(r'^accounts/profile/(?P<pk>\d+)/edit/$', login_required(nature_views.UserSettingsView.as_view(template_name='nature/base_profile_form.html')), name='profile-edit'),
    #view the profile to actually be useful
    re_path(r'^accounts/profile/(?P<username>\w+)/$', nature_views.user_profile, name='user-profile'),
    re_path(r'^accounts/profile/(?P<pk>\d+)/', login_required(nature_views.UserDetailView.as_view(template_name='nature/base_profile.html'))),
    #view the profile to actually be useful
    re_path(r'^accounts/profile/$', login_required(nature_views.UserDetailView.as_view(template_name='nature/base_profile.html'))),
    #check for invites
    re_path(r'^accounts/invites/$', login_required(nature_views.UserInvitesView.as_view(template_name='nature/base_invites.html'))),
    #get a total invites for a user
    re_path(r'^accounts/invites/count/(?P<user>\d+)/$', nature_views.get_invite_count, name='invite-count'),
    re_path(r'^accounts/invites/list/(?P<user>\d+)/$', nature_views.get_invite_list, name='invite-list'),
    #accept/reject the invitation
    re_path(r'^accounts/invites/(?P<group>\d+)/(?P<response>\d+)/$', nature_views.group_invite_response, name='group-invite-response'),
    #all other accounts/ url functions go to the registration module
    # re_path(r'^accounts/register/$', RegistrationView.as_view(form_class=UserRegistrationForm), name='registration_register'),
    re_path(r'^accounts/', include('django_registration.backends.activation.urls')),
    #list/ is for lists/courses
    re_path(r'^list/(?P<pk>\d+)/', login_required(nature_views.CourseView.as_view()), name='course-view'),
    re_path(r'^list/$', login_required(nature_views.CourseList.as_view()), name='course-list'),
    #add/list/ is to create a new list
    re_path(r'^add/list/$', login_required(nature_views.CourseCreateView.as_view(template_name='nature/base_course_create.html')), name='course-add'),
    #add a single item to an existing list
    re_path(r'^add/list/(?P<course>\d+)/item/(?P<organism>\d+)/$', nature_views.add_list_item, name='course-add-item'),
    #copy someone else's list to your userid
    re_path(r'^copy/list/(?P<course>\d+)/$', nature_views.copy_list, name='course-copy'),
    #edit the list
    re_path(r'^edit/list/(?P<pk>\d+)/$', login_required(nature_views.CourseUpdate.as_view(template_name='nature/base_course_update.html')), name='course-edit'),
    #this will delete a single organism from a list
    re_path(r'^delete/list/item/(?P<pk>\d+)/$', nature_views.delete_list_item, name='delete-course-item'),
    #this will delete an entire list
    re_path(r'^delete/list/(?P<pk>\d+)/$', nature_views.delete_list, name='delete-list'),
    #group/ is for a specific group
    re_path(r'^group/(?P<pk>\d+)/', login_required(nature_views.GroupView.as_view()), name='group-view'),
    re_path(r'^group/$', login_required(nature_views.GroupList.as_view()), name='group-list'),
    #add/group/ is to create a new group
    re_path(r'^add/group/$', login_required(nature_views.GroupCreateView.as_view(template_name='nature/base_group_create.html')), name='group-add'),
    #add a single item to an existing group
    re_path(r'^add/group/(?P<group>\d+)/user/(?P<user>\d+)/(?P<status>\d+)/$', nature_views.add_group_user, name='group-invite'),
    #edit the group
    re_path(r'^edit/group/(?P<pk>\d+)/$', login_required(nature_views.GroupUpdate.as_view(template_name='nature/base_group_update_head.html')), name='group-edit'),
    #this will delete a single organism from a group
    re_path(r'^delete/group/user/(?P<pk>\d+)/$', nature_views.delete_group_user, name='group-delete-user'),
    #this will delete an entire group
    re_path(r'^delete/group/(?P<pk>\d+)/$', nature_views.delete_group, name='group-delete'),
    #this gets a list of groups for the user
    re_path(r'^group/user/(?P<user>\d+)/$', nature_views.get_user_groups, name='group-user-list'),
    #location/ is for locations
    re_path(r'^location/(?P<pk>\d+)/', nature_views.LocationView.as_view(), name='location-view'),  
    re_path(r'^location/$', nature_views.LocationList.as_view(template_name='nature/base_location_list.html'), name='location-home'),
    re_path(r'^add/location/$', login_required(nature_views.LocationCreate.as_view(template_name='nature/base_location_form.html')), name='location-add'),
    re_path(r'^edit/location/(?P<pk>\d+)/$', login_required(nature_views.LocationUpdate.as_view(template_name='nature/base_location_update.html')), name='location-edit'),
    #this will delete an entire location
    re_path(r'^delete/location/(?P<pk>\d+)/$', nature_views.delete_location, name='location-delete'),
    #automplete all pass to the same view
    re_path(r'^autocomplete/$',nature_views.autocomplete, name='nature-autocomplete'),
    re_path(r'autocomplete/haystack/$', nature_views.autocomplete, name='haystack-autocomplete'),
    #stats/
    re_path(r'stats/$', nature_views.StatsView.as_view(template_name='nature/base_stats.html')),
    #this is currently where you end up after submitting any forms....
    re_path(r'thanks/', nature_views.thanks, name='thanks'),
    re_path(r'noresults/', TemplateView.as_view(template_name = 'nature/base_noresults.html'), name='no-results'),
    #discover
    #re_path(r'^discover/organism/', include('haystack.urls')),
    re_path(r'^discover/(?P<search>\w+)/$', nature_views.DiscoverList.as_view(), name='discover'),
    re_path(r'^contact/', include('django_contact_form.urls')),
    re_path(r'^blog/', include('zinnia.urls', namespace='zinnia')),
]