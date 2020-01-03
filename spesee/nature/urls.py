from django.conf.urls import *
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
    url(r'^djangojs/', include('djangojs.urls')),
    #home page
    url(r'^$', nature_views.IndexListView.as_view(), name='home-page'),
    url(r'^$', nature_views.IndexListView.as_view(), name='my-books'),
    #about page
    url(r'^about/$', TemplateView.as_view(template_name = 'nature/base_about.html'), name='about-page'),
    #organism type details
    url(r'^type/(?P<pk>\d+)/',DetailView.as_view(model=OrganismType, template_name='nature/type.html'), name='type-view'),
    #list of types
    url(r'^type/', ListView.as_view(model=OrganismType, context_object_name='type_list', template_name='nature/base_type.html')),
    #org tag types
    url(r'^tags/type/(?P<org_type>\d+)/$', nature_views.type_tags, name='nature-type-tags'),
    #organism tagging
    url(r'^tags/organism/(?P<organism>\d+)/$', nature_views.organism_tags, name='organism-tags'),
    #search tags
    url(r'^tags/search/(?P<type>[\w]+)/(?P<tag>[\s\w]+)/$',nature_views.TagListView.as_view(), name='nature-search-tags'),
    #save tags
    url(r'^save/tags/organism/(?P<organism>\d+)/$', nature_views.save_tags, name='nature-save-tags'),
    #save org ident
    url(r'^save/organism/ident/', nature_views.save_org_ident, name='save-org-ident'),
    #/organism/
    url(r'^organism/(?P<pk>\d+)/', nature_views.OrganismView.as_view(), name='organism-view'),
    url(r'^test/organism/(?P<pk>\d+)/', nature_views.OrganismViewTest.as_view(), name='organism-view-test'),
    #/check for existing obs for that org/lat/lng
    url(r'^check/(?P<search_type>\w+)/(?P<search_value>\d+)/', nature_views.check_existing, name='check-existing'),
    url(r'^review/$', nature_views.ReviewHome.as_view(), name='nature-review-home'),
    #list organism changes to be reviewed
    url(r'^review/organism/$', nature_views.OrgIdentReviewList.as_view(), name='review-organism-list'),
    #specific item to be reviewed
    url(r'^review/organism/(?P<pk>\d+)/$', nature_views.OrgIdentReview.as_view(), name='review-organism-view'),
    #obs to be reviewed
    url(r'^review/observation/$', nature_views.ObservationReviewList.as_view(), name='review-obs-list'),
    #specific obs to be reviewed
    url(r'^review/observation/(?P<pk>\d+)/$', nature_views.ObservationReview.as_view(), name='review-obs'),
    #list of images to be reviewed
    url(r'^review/images/$', nature_views.ImagesReviewList.as_view(), name='review-image-list'),
    #specific image to be reviewed
    url(r'^review/images/(?P<pk>\d+)/$', nature_views.ImagesReviewUpdate.as_view(), name='review-image'),
    #upload an image
    url(r'^organism/image/upload/(?P<pk>\d+)/$', nature_views.ImageUpload.as_view(), name='image-upload'),
    #get images for an organism to add to the ident details
    url(r'^organism/image/(?P<organism>\d+)/$', nature_views.get_org_images, name='image-list'),
    #build a search page
    #this section is currently commented out to avoid interfering with haystack. I may keep these features, but I need to move them.
    #url(r'^search/$', ListView.as_view(
    #        model=OrganismType,
    #        context_object_name='type_list',
    #        template_name='nature/base_search.html')),
    #get the id_fields from the selected type
    #url(r'^search/(?P<type_name>\w+)/$', nature_views.get_ident_fields', name='type_search'),
    #get the id_detail values from the id_field/type selected
    #url(r'^search/(?P<type_name>\w+)/(?P<id_field>[\s\w]+)/$', nature_views.get_ident_details', name='id_field_search'),
    #ident/is for ident fields (shows organisms with a certain value in an particular ident field)
    #so, for example you might want to find Birds(type) with a color(ident field) of White (details)
    # url(r'^ident/(\w+)/([\s\w]+)/([\s\w]+)/$',    
    #     IdentDetailListView.as_view(), name='search-ident'),
    #haystack search urls
    url(r'^search/', include('haystack.urls')),
    #observations by user, zip, etc
    url(r'^observation/(?P<search>\w+)/(?P<pk>\d+)/$', login_required(nature_views.ObservationList.as_view()), name='observation-list'),
    #observation/$ shows all observations for the user logged in
    url(r'^observation/$', login_required(nature_views.ObservationListSelf.as_view()), name="observation-home"),
    #observation/(?<pk>\d+) displays a specific observation
    url(r'^observation/(?P<pk>\d+)/$', DetailView.as_view(queryset = Observation.objects.select_related(), context_object_name='observation', template_name='nature/base_observation.html'), name='observation-detail'),
    #edit/observation/(?<pk>\d+)/ is for a user to edit their own observation
    url(r'^edit/observation/(?P<pk>\d+)/$', login_required(nature_views.ObservationUpdateView.as_view(template_name='nature/base_observation_form.html')), name='edit-observation'),
    #add/observation/ is to add an observation
    url(r'^add/observation/$', login_required(nature_views.ObservationCreateView.as_view(template_name='nature/base_observation_form.html')), name='add-observation'),
    #export my observations
    url(r'observation/export/$', nature_views.export_obs, name='export-observations'),
    #shows the login screen
    url(r'^accounts/login/$', auth_views.LoginView, {'template_name': 'nature/base_login.html'}, name='account-login'),
    url(r'^accounts/login/simple/$', nature_views.login, name='login-simple'),
    #logout the user
    url(r'^accounts/logout/$', auth_views.LogoutView, {'template_name': 'nature/base_logged_out.html'}, name='account-logout'),
    #shows the user profile page
    url(r'^accounts/profile/(?P<pk>\d+)/edit/$', login_required(nature_views.UserSettingsView.as_view(template_name='nature/base_profile_form.html')), name='profile-edit'),
    #view the profile to actually be useful
    url(r'^accounts/profile/(?P<username>\w+)/$', nature_views.user_profile, name='user-profile'),
    url(r'^accounts/profile/(?P<pk>\d+)/', login_required(nature_views.UserDetailView.as_view(template_name='nature/base_profile.html'))),
    #view the profile to actually be useful
    url(r'^accounts/profile/$', login_required(nature_views.UserDetailView.as_view(template_name='nature/base_profile.html'))),
    #check for invites
    url(r'^accounts/invites/$', login_required(nature_views.UserInvitesView.as_view(template_name='nature/base_invites.html'))),
    #get a total invites for a user
    url(r'^accounts/invites/count/(?P<user>\d+)/$', nature_views.get_invite_count, name='invite-count'),
    url(r'^accounts/invites/list/(?P<user>\d+)/$', nature_views.get_invite_list, name='invite-list'),
    #accept/reject the invitation
    url(r'^accounts/invites/(?P<group>\d+)/(?P<response>\d+)/$', nature_views.group_invite_response, name='group-invite-response'),
    #all other accounts/ url functions go to the registration module
    # url(r'^accounts/register/$', RegistrationView.as_view(form_class=UserRegistrationForm), name='registration_register'),
    url(r'^accounts/', include('django_registration.backends.activation.urls')),
    #list/ is for lists/courses
    url(r'^list/(?P<pk>\d+)/', login_required(nature_views.CourseView.as_view()), name='course-view'),
    url(r'^list/$', login_required(nature_views.CourseList.as_view()), name='course-list'),
    #add/list/ is to create a new list
    url(r'^add/list/$', login_required(nature_views.CourseCreateView.as_view(template_name='nature/base_course_create.html')), name='course-add'),
    #add a single item to an existing list
    url(r'^add/list/(?P<course>\d+)/item/(?P<organism>\d+)/$', nature_views.add_list_item, name='course-add-item'),
    #copy someone else's list to your userid
    url(r'^copy/list/(?P<course>\d+)/$', nature_views.copy_list, name='course-copy'),
    #edit the list
    url(r'^edit/list/(?P<pk>\d+)/$', login_required(nature_views.CourseUpdate.as_view(template_name='nature/base_course_update.html')), name='course-edit'),
    #this will delete a single organism from a list
    url(r'^delete/list/item/(?P<pk>\d+)/$', nature_views.delete_list_item, name='delete-course-item'),
    #this will delete an entire list
    url(r'^delete/list/(?P<pk>\d+)/$', nature_views.delete_list, name='delete-list'),
    #group/ is for a specific group
    url(r'^group/(?P<pk>\d+)/', login_required(nature_views.GroupView.as_view()), name='group-view'),
    url(r'^group/$', login_required(nature_views.GroupList.as_view()), name='group-list'),
    #add/group/ is to create a new group
    url(r'^add/group/$', login_required(nature_views.GroupCreateView.as_view(template_name='nature/base_group_create.html')), name='group-add'),
    #add a single item to an existing group
    url(r'^add/group/(?P<group>\d+)/user/(?P<user>\d+)/(?P<status>\d+)/$', nature_views.add_group_user, name='group-invite'),
    #edit the group
    url(r'^edit/group/(?P<pk>\d+)/$', login_required(nature_views.GroupUpdate.as_view(template_name='nature/base_group_update_head.html')), name='group-edit'),
    #this will delete a single organism from a group
    url(r'^delete/group/user/(?P<pk>\d+)/$', nature_views.delete_group_user, name='group-delete-user'),
    #this will delete an entire group
    url(r'^delete/group/(?P<pk>\d+)/$', nature_views.delete_group, name='group-delete'),
    #this gets a list of groups for the user
    url(r'^group/user/(?P<user>\d+)/$', nature_views.get_user_groups, name='group-user-list'),
    #location/ is for locations
    url(r'^location/(?P<pk>\d+)/', nature_views.LocationView.as_view(), name='location-view'),  
    url(r'^location/$', nature_views.LocationList.as_view(template_name='nature/base_location_list.html'), name='location-home'),
    url(r'^add/location/$', login_required(nature_views.LocationCreate.as_view(template_name='nature/base_location_form.html')), name='location-add'),
    url(r'^edit/location/(?P<pk>\d+)/$', login_required(nature_views.LocationUpdate.as_view(template_name='nature/base_location_update.html')), name='location-edit'),
    #this will delete an entire location
    url(r'^delete/location/(?P<pk>\d+)/$', nature_views.delete_location, name='location-delete'),
    #automplete all pass to the same view
    url(r'^autocomplete/$',nature_views.autocomplete, name='nature-autocomplete'),
    url(r'autocomplete/haystack/$', nature_views.autocomplete, name='haystack-autocomplete'),
    #stats/
    url(r'stats/$', nature_views.StatsView.as_view(template_name='nature/base_stats.html')),
    #this is currently where you end up after submitting any forms....
    url(r'thanks/', nature_views.thanks, name='thanks'),
    url(r'noresults/', TemplateView.as_view(template_name = 'nature/base_noresults.html'), name='no-results'),
    #discover
    #url(r'^discover/organism/', include('haystack.urls')),
    url(r'^discover/(?P<search>\w+)/$', nature_views.DiscoverList.as_view(), name='discover'),
    url(r'^contact/', include('contact_form.urls')),
    url(r'^blog/', include('zinnia.urls', namespace='zinnia')),
]