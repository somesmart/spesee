from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required
from django.views.generic import DetailView, ListView, UpdateView, CreateView, DeleteView
from django.db.models import Count
from mysite.nature.models import *
from mysite.nature.views import *
from mysite.nature.signals import *
from registration.views import register
import registration.backends.default.urls as regUrls
import mysite.nature.signals

urlpatterns = patterns('',
    #home page
    url(r'^$',
        ListView.as_view(
            queryset=Organism.objects.select_related().annotate(observed=Count('observation__id')).order_by('-observation__observation_date')[:10],
            context_object_name='first_ogranisms',
            template_name='nature/index.html')),
    #organism type details
    url(r'^type/(?P<pk>\d+)/',
        DetailView.as_view(
            model=OrganismType,
            template_name='nature/type.html')),
    #list of types
    url(r'^type/',
        ListView.as_view(
            model=OrganismType,
            context_object_name='type_list',
            template_name='nature/base_type.html')),
    #save org ident
    url(r'^save/organism/ident/', 'mysite.nature.views.save_org_ident', name='save-org-ident'),
    #/organism/
    url(r'^organism/(?P<pk>\d+)/',
        OrganismView.as_view(), name='organism-view'),
    url(r'^test/organism/(?P<pk>\d+)/',
        OrganismViewTest.as_view(), name='organism-view-test'),
    #/check for existing obs for that org/lat/lng
    url(r'^check/(?P<search_type>\w+)/(?P<search_value>\d+)/', 'mysite.nature.views.check_existing', name='check-existing'),
    url(r'^review/$',
        ReviewHome.as_view(), name='review-home'),
    #list organism changes to be reviewed
    url(r'^review/organism/$',
        OrgIdentReviewList.as_view(), name='review-list'),
    #specific item to be reviewed
    url(r'^review/organism/(?P<pk>\d+)/$',
        OrgIdentReview.as_view(), name='review-organism'),
    #list of images to be reviewed
    url(r'^review/images/$',
        ImagesReviewList.as_view(), name='review-image-list'),
    #specific image to be reviewed
    url(r'^review/images/(?P<pk>\d+)/$',
        ImagesReviewUpdate.as_view(), name='review-image'),
    #upload an image
    url(r'^organism/image/upload/(?P<pk>\d+)/$',
        ImageUpload.as_view(), name='image-upload'),
    #get images for an organism to add to the ident details
    url(r'^organism/image/(?P<organism>\d+)/$', 'mysite.nature.views.get_org_images', name='image-list'),
    #build a search page
    #this section is currently commented out to avoid interfering with haystack. I may keep these features, but I need to move them.
    #url(r'^search/$', ListView.as_view(
    #        model=OrganismType,
    #        context_object_name='type_list',
    #        template_name='nature/base_search.html')),
    #get the id_fields from the selected type
    #url(r'^search/(?P<type_name>\w+)/$', 'mysite.nature.views.get_ident_fields', name='type_search'),
    #get the id_detail values from the id_field/type selected
    #url(r'^search/(?P<type_name>\w+)/(?P<id_field>[\s\w]+)/$', 'mysite.nature.views.get_ident_details', name='id_field_search'),
    #ident/is for ident fields (shows organisms with a certain value in an particular ident field)
    #so, for example you might want to find Birds(type) with a color(ident field) of White (details)
    url(r'^ident/(\w+)/([\s\w]+)/([\s\w]+)/$',    
        IdentDetailListView.as_view(), name='search-ident'),
    #haystack search urls
    (r'^search/', include('haystack.urls')),
    #observations by user, zip, etc
    url(r'^observation/(?P<search>\w+)/(?P<pk>\d+)/$',
        login_required(ObservationList.as_view()), name='observation-list'),
    #observation/$ shows all observations for the user logged in
    url(r'^observation/$',
        login_required(ObservationListSelf.as_view())),
    #observation/(?<pk>\d+) displays a specific observation
    url(r'^observation/(?P<pk>\d+)/$',
        DetailView.as_view(
            queryset = Observation.objects.select_related(),
            template_name='nature/base_observation.html'), name='observation-detail'),
    #edit/observation/(?<pk>\d+)/ is for a user to edit their own observation
    url(r'^edit/observation/(?P<pk>\d+)/$',
        login_required(ObservationUpdateView.as_view(
            template_name='nature/base_observation_form.html')), name='edit-observation'),
    #add/observation/ is to add an observation
    url(r'^add/observation/$',
        login_required(ObservationCreateView.as_view(
            template_name='nature/base_observation_form.html')), name='add-observation'),
    #shows the login screen
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'nature/base_login.html'}, name='account-login'),
    url(r'^accounts/login/simple/$', 'mysite.nature.views.login', name='login-simple'),
    #logout the user
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'template_name': 'nature/base_logged_out.html'}, name='account-logout'),
    #shows the user profile page
    (r'^accounts/profile/(?P<pk>\d+)/edit/$',
        login_required(UserSettingsView.as_view(
            template_name='nature/base_profile_form.html'))),
    #view the profile to actually be useful
    (r'^accounts/profile/(?P<pk>\d+)/',
        login_required(UserDetailView.as_view(
            template_name='nature/base_profile.html'))),
    url(r'^accounts/profile/(?P<username>\w+)/$', 'mysite.nature.views.user_profile', name='user-profile'),
    #view the profile to actually be useful
    (r'^accounts/profile/$',
        login_required(UserDetailView.as_view(
            template_name='nature/base_profile.html'))),
    #check for invites
    (r'^accounts/invites/$',
        login_required(UserInvitesView.as_view(
            template_name='nature/base_invites.html'))),
    #get a total invites for a user
    url(r'^accounts/invites/count/(?P<user>\d+)/$', 'mysite.nature.views.get_invite_count', name='invite-count'),
    url(r'^accounts/invites/list/(?P<user>\d+)/$', 'mysite.nature.views.get_invite_list', name='invite-list'),
    #accept/reject the invitation
    url(r'^accounts/invites/(?P<group>\d+)/(?P<response>\d+)/$', 'mysite.nature.views.group_invite_response'),
    #for registration form override
    url(r'^accounts/register/$', register, {'backend': 'registration.backends.default.DefaultBackend','form_class': UserRegistrationForm}, name='registration_register'),
    #all other accounts/ url functions go to the registration module
    (r'^accounts/', include('registration.backends.default.urls')),
    #list/ is for lists/courses
    url(r'^list/(?P<pk>\d+)/',
        login_required(CourseView.as_view()), name='course-view'),
    url(r'^list/$',
        login_required(CourseList.as_view()), name='course-list'),
    #add/list/ is to create a new list
    ##########################
    #add the ability to copy someone's course to your own
    url(r'^add/list/$',
        login_required(CourseCreateView.as_view(
            template_name='nature/base_course_create.html')), name='list-add'),
    #add a single item to an existing list
    url(r'^add/list/(?P<course>\d+)/item/(?P<organism>\d+)/$', 'mysite.nature.views.add_list_item'),
    #edit the list
    url(r'^edit/list/(?P<pk>\d+)/$',
        login_required(CourseUpdate.as_view(
            template_name='nature/base_course_update.html'))),
    #this will delete a single organism from a list
    url(r'^delete/list/item/(?P<pk>\d+)/$', 'mysite.nature.views.delete_list_item'),
    #this will delete an entire list
    url(r'^delete/list/(?P<pk>\d+)/$', 'mysite.nature.views.delete_list'),
    #group/ is for a specific group
    url(r'^group/(?P<pk>\d+)/',
        login_required(GroupView.as_view()), name='group-view'),
    url(r'^group/$',
        login_required(GroupList.as_view()), name='group-list'),
    #add/group/ is to create a new group
    url(r'^add/group/$',
        login_required(GroupCreateView.as_view(
            template_name='nature/base_group_create.html')), name='group-add'),
    #add a single item to an existing group
    url(r'^add/group/(?P<group>\d+)/user/(?P<user>\d+)/(?P<status>\d+)/$', 'mysite.nature.views.add_group_user', name='group-invite'),
    #edit the group
    url(r'^edit/group/(?P<pk>\d+)/$', login_required(GroupUpdate.as_view(template_name='nature/base_group_update_head.html')), name='group-edit'),
    #this will delete a single organism from a group
    url(r'^delete/group/user/(?P<pk>\d+)/$', 'mysite.nature.views.delete_group_user'),
    #this will delete an entire group
    url(r'^delete/group/(?P<pk>\d+)/$', 'mysite.nature.views.delete_group'),
    #this gets a list of groups for the user
    url(r'^group/user/(?P<user>\d+)/$', 'mysite.nature.views.get_user_groups'),
    #this is how we could do passing the type of map (zip code) then the search value (zip pk)
    url(r'^map/(?P<maptype>\w+)/(?P<pk>\d+)/$',
         MapView.as_view(), name='map-data'),
    #location/ is for locations
    url(r'^location/(?P<pk>\d+)/', 
        LocationView.as_view(), name='location-view'),  
    url(r'^location/$', LocationList.as_view(
            template_name='nature/base_location_list.html')),
    url(r'^add/location/$', 
        login_required(LocationCreate.as_view(
            template_name='nature/base_location_form.html')), name='location-add'),
    url(r'^edit/location/(?P<pk>\d+)/$', 
        login_required(LocationUpdate.as_view(
            template_name='nature/base_location_update.html'))),
    #this will delete an entire location
    url(r'^delete/location/(?P<pk>\d+)/$', 'mysite.nature.views.delete_location'),
    #automplete all pass to the same view
    url(r'autocomplete/$','mysite.nature.views.autocomplete', name='autocomplete'),
    url(r'autocomplete/haystack/$', 'mysite.nature.views.autocomplete', name='haystack-autocomplete'),
    #stats/
    url(r'stats/$', StatsView.as_view(
        template_name='nature/base_stats.html')),
    #this is currently where you end up after submitting any forms....
    url(r'thanks/', 'mysite.nature.views.thanks', name='thanks'),
    #zinnia
    url(r'^blog/', include('zinnia.urls')),
    url(r'^blog/tags/', include('zinnia.urls.tags')),
    url(r'^blog/feeds/', include('zinnia.urls.feeds')),
    url(r'^blog/authors/', include('zinnia.urls.authors')),
    url(r'^blog/categories/', include('zinnia.urls.categories')),
    url(r'^blog/discussions/', include('zinnia.urls.discussions')),
    url(r'^blog/', include('zinnia.urls.entries')),
    url(r'^blog/', include('zinnia.urls.archives')),
    url(r'^blog/', include('zinnia.urls.shortlink')),
    url(r'^blog/', include('zinnia.urls.quick_entry')),
    url(r'^comments/', include('django.contrib.comments.urls')),
    #discover
    #url(r'^discover/organism/', include('haystack.urls')),
    url(r'^discover/(?P<search>\w+)/$', DiscoverList.as_view(), name='discover'),
)