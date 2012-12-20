from django.db import models
from django.core.urlresolvers import reverse
import datetime
from django.contrib.auth.models import User
import os
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Adjust
# from moderation import moderation

# *********************************************************************** #
# **************************set up/meta data **************************** #
# *********************************************************************** #

#where the different types of organisms (Bird, Tree, Amphibian) are stored
class OrganismType(models.Model):
	description = models.CharField(max_length=200)
	def __unicode__(self):
		return self.description
	def get_absolute_url(self):
		return "/type/%i/" % self.id 	

class IdentificationField(models.Model):
	type = models.ForeignKey(OrganismType, related_name="id_fields")
	name = models.CharField(max_length=200)

	def __unicode__(self):
		return self.name

class Family(models.Model):
	family_name = models.CharField(max_length=200)
	family_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.family_name
	def __unicode__(self):
		return self.family_descr	
	class Meta:
		verbose_name_plural = "families"

class Order(models.Model):
	order_name = models.CharField(max_length=200)
	order_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.order_name
	def __unicode__(self):
		return self.order_descr

class Sp_Class(models.Model):
	sp_class_name = models.CharField(max_length=200)
	sp_class_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.sp_class_name
	def __unicode__(self):
		return self.sp_class_descr
	class Meta:
		verbose_name = "class"
		verbose_name_plural = "classes"	

class Phylum(models.Model):
	phylum_name = models.CharField(max_length=200)
	phylum_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.phylum_name
	def __unicode__(self):
		return self.phylum_descr

class Kingdom(models.Model):
	kingdom_name = models.CharField(max_length=200)
	kingdom_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.kingdom_name
	def __unicode__(self):
		return self.kingdom_descr

class PopulationStatus(models.Model):
	status_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.status_descr
	class Meta:
		verbose_name_plural = "population statuses"	

class StateStatus(models.Model):
	status_descr = models.CharField(max_length=200)
	def __unicode__(self):
		return self.status_descr
	class Meta:
		verbose_name_plural = "state statuses"

class Region(models.Model):
	region_name = models.CharField(max_length=200)
	def __unicode__(self):
		return self.region_name

class State(models.Model):
	state = models.CharField(max_length=50)
	def __unicode__(self):
		return self.state

class ZipCode(models.Model):
	zipcode = models.CharField(max_length=5)
	latitude = models.DecimalField(max_digits=15, decimal_places=9)
	longitude = models.DecimalField(max_digits=15, decimal_places=9)
	state = models.ForeignKey(State, related_name="state_zip")
	county = models.CharField(max_length=100)
	country = models.CharField(max_length=100)
	def __unicode__(self):
		return self.county
	def __unicode__(self):
		return self.country
	def __unicode__(self):
		return self.zipcode	

# need to add leaf morphology, seasonality, color, flower, and fruit models
# may actually need to store all possible identification options in a single model, 
# and then restrict the forms to only display the appropriate one? Not sure yet
# probably want to use the limit_choices_to somehow, or a custom method
# one solution could be to set the possible identification fields in a table
# which the OrganismType references as a ForeignKey
# and then the identificationdetails can reference descr in (for example) the 
# Color model, which has identification_type as a Foreign key?

# ****************************************************************** #
# ********************* organism/detail data *********************** #
# ****************************************************************** #

class Organism(models.Model):
	common_name = models.CharField(max_length=200)
	latin_name = models.CharField(max_length=200)
	population_status = models.ForeignKey(PopulationStatus, related_name="org_pop_status")
	family = models.ForeignKey(Family, related_name="org_family")
	order = models.ForeignKey(Order, related_name="org_order")
	sp_class = models.ForeignKey(Sp_Class, related_name="org_class")
	phylum = models.ForeignKey(Phylum, related_name="org_phylum")
	kingdom = models.ForeignKey(Kingdom, related_name="org_kingdom")
	type = models.ForeignKey(OrganismType, related_name="organisms")
	ident_tips = models.TextField('identification tips', blank=True)
	habitat_descr = models.TextField('habitat description', blank=True)
	image = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
	#this kind of works but it seems to store a record for each ident_field...
	#history = HistoricalRecords()

	def get_absolute_url(self):
		return "/organism/%i/" % self.id 
	def get_edit_url(self):
		return	"/edit/organism/%i/" % self.id 
	def get_map_url(self):
		return "/map/organism/%i/" % self.id
	def get_add_ident(self):
		return "/add/organism/ident/%i/" % self.id
	def get_edit_ident(self):
		return "/edit/organism/ident/%i/" % self.id

	def __unicode__(self):
		return u"%s (%s)" % (self.common_name, self.latin_name)

	def save(self, *args, **kwargs):
		# Ensures the latin_name is always "Singleupcase otherslowercase"
		self.latin_name = self.latin_name[0].upper() + self.latin_name[1:].lower()
		return super(Organism, self).save(*args, **kwargs)
	class Meta:
		ordering=["common_name"]	

#stores the large, moderated text field users edit for helping with identification
class OrgIdentification(models.Model):
	organism = models.ForeignKey(Organism, related_name='org_ident', unique=True)
	identification = models.TextField(blank=True)
	#may want to add "last edit date, last edit user, etc"?
	def get_absolute_url(self):
		return "/organism/%i/" % self.organism.id
	def __unicode__(self):
		return self.identification


#stores the updated/created values for OrgIdentifications under review and the history
class OrgIdentificationReview(models.Model):
	STATUS_CHOICES = (
        (1, 'Approved'),
        (2, 'Pending'),
        (3, 'Rejected'),
    )
	organism = models.ForeignKey(Organism)
	identification = models.TextField(blank=True)
	modified_by = models.ForeignKey(User, related_name='+')
	modified_date = models.DateTimeField()
	status = models.IntegerField(choices=STATUS_CHOICES) #1 - Approved; 2 - Pending; 3 - Rejected
	reason = models.TextField(blank=True)
	moderated_by = models.ForeignKey(User, related_name='+', null=True, default=None, blank=True)
	moderated_date = models.DateTimeField(null=True, default=None, blank=True)
	def __unicode__(self):
		return self.identification
	def __unicode__(self):
		return self.reason


#store the identification fields for that organism (i.e. a leaf type)
class IdentificationDetail(models.Model):
	organism = models.ForeignKey(Organism, related_name="id_details")
	field = models.ForeignKey(IdentificationField, related_name="id_field_details")
	description = models.CharField(max_length=250)
	def __unicode__(self):
		return u"%s is %s" % (self.field.name, self.description)
	#consider doing a def save here to store the description slugified...
	class Meta:
		verbose_name_plural = "identification details"

#you can specify a specific location, and then see observations within the range as defined
#by the miles wide and miles tall
#the map by location will create a range using .014 lat/lng per mile
class Location(models.Model):
	name = models.CharField(max_length=100)
	description = models.TextField(blank=True)
	latitude = models.DecimalField(max_digits=11, decimal_places=9)
	longitude = models.DecimalField(max_digits=11, decimal_places=9)
	miles_wide = models.DecimalField(max_digits=7, decimal_places=2)
	miles_tall = models.DecimalField(max_digits=7, decimal_places=2)
	created_by = models.ForeignKey(User, related_name="+")
	private = models.BooleanField()
	def __unicode__(self):
		return self.description
	def __unicode__(self):
		return self.name

	def get_absolute_url(self):
		return "/location/%i/" % self.id
	def get_edit_url(self):
		return "/edit/location/%i/" % self.id
	def get_map_url(self):
		return "/map/location/%i/" % self.id

#need to add a model/way to subscribe or follow other people's locations

#store the regions where an organism can be found
class OrgRegion(models.Model):
	organism = models.ForeignKey(Organism, related_name="org_regions")
	region = models.ForeignKey(Region, related_name="region_details")
	class Meta:
		verbose_name = "organism region"

#stores the endangered status of an organism for a particular state
class OrgStateStatus(models.Model):	
	organism = models.ForeignKey(Organism, related_name="org_states")
	state = models.ForeignKey(State, related_name="state_details")
	state_status = models.ForeignKey(StateStatus, related_name="state_status_details")
	class Meta:
		verbose_name = "organism state status"
		verbose_name_plural = "organism state statuses"

#stores the observation details for an observation event
class Observation(models.Model):
	organism = models.ForeignKey(Organism)
	user = models.ForeignKey(User, related_name="+")
	observation_date = models.DateTimeField()
	temperature = models.DecimalField(max_digits=5, decimal_places=2)
	latitude = models.DecimalField(max_digits=11, decimal_places=9)
	longitude = models.DecimalField(max_digits=11, decimal_places=9)
	location_descr = models.CharField('description of location', max_length=200)
	comments = models.CharField(max_length=200)
	quantity = models.IntegerField()
	observation_image = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
	parent_observation = models.ForeignKey('self', blank=True, default=None, null=True, help_text='The first observation of a static organism', related_name='child_observation')
	thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(50, 50)], image_field='observation_image', format='JPEG', options={'quality': 90})
	large_image = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(500, 400)], image_field='observation_image', format='JPEG', options={'quality': 90})
	wide_thumb = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(200, 100)], image_field='observation_image', format='JPEG', options={'quality': 90})
	def __unicode__(self):
		return self.location_descr
	def __unicode__(self):
		return self.comments	
	def get_absolute_url(self):
		return "/observation/%i/" % self.id 	
	def get_edit_url(self):
		return "/edit/observation/%i/" % self.id
	def get_map_url(self):
		return "/map/observation/%i/" % self.id
	# def get_add_specific_url(self):
	# 	return "/observation/?org=%i/" % self.id

class Images(models.Model):
	def get_image_path(instance, filename):
		return os.path.join('photos/organism', str(instance.organism.id), filename)
	STATUS_CHOICES = (
        (1, 'Approved'),
        (2, 'Pending'),
        (3, 'Rejected'),
    )
	org_image = models.ImageField(upload_to=get_image_path, blank=True)
	thumbnail = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(50, 50)], image_field='org_image', format='JPEG', options={'quality': 90})
	large_image = ImageSpecField([Adjust(contrast=1.2, sharpness=1.1), ResizeToFill(500, 400)], image_field='org_image', format='JPEG', options={'quality': 90})
	upload_date = models.DateTimeField()
	upload_user = models.ForeignKey(User, related_name="+")
	organism = models.ForeignKey(Organism)
	caption = models.CharField(max_length=200, null=True, default=None, blank=True)
	status = models.IntegerField(choices=STATUS_CHOICES, default=2) #1 - Approved; 2 - Pending; 3 - Rejected
	primary_image = models.BooleanField()
	def __unicode__(self):
		return self.caption		

#stores the updated/created values for Images under review and the history
class ImagesReview(models.Model):
	STATUS_CHOICES = (
        (1, 'Approved'),
        (2, 'Pending'),
        (3, 'Rejected'),
    )
	review_image = models.ForeignKey(Images)
	modified_by = models.ForeignKey(User, related_name='+')
	modified_date = models.DateTimeField()
	status = models.IntegerField(choices=STATUS_CHOICES) #1 - Approved; 2 - Pending; 3 - Rejected
	reason = models.TextField(blank=True)
	moderated_by = models.ForeignKey(User, related_name='+', null=True, default=None, blank=True)
	moderated_date = models.DateTimeField(null=True, default=None, blank=True)
	primary_image = models.BooleanField()
	def __unicode__(self):
		return self.reason

# **************************************************************** #
# ********************** group set up **************************** #
# **************************************************************** #		

class Group(models.Model):
	name = models.CharField(max_length=200)
	private = models.BooleanField()
	owner = models.ForeignKey(User, related_name='+')
	def __unicode__(self):
		return self.name
	def get_add_url(self):
		return "/add/group/"
	def get_absolute_url(self):
		return "/group/%i/" % self.id 

class GroupUsers(models.Model):
	user = models.ForeignKey(User, related_name='+')
	group = models.ForeignKey(Group, related_name='group_users')
	#status 1 active member 2 invited member
	#people can auto-join public groups
	status = models.IntegerField()		

# ************************************************************** #
# *********************** courses data ************************* #
# ************************************************************** #

#stores the course master data
class Course(models.Model):
	course_name = models.CharField(max_length=200)
	course_descr = models.CharField(max_length=200)
	user = models.ForeignKey(User, related_name="+") #this is the person who created it, and it will always be here
	is_group = models.BooleanField()
	group = models.ForeignKey(Group, null=True, default=None, blank=True)
	def __unicode__(self):
		return self.course_name
	def __unicode__(self):
		return self.course_descr
	def get_absolute_url(self):
		return "/list/%i/" % self.id 	
	def get_edit_url(self):
		return "/edit/list/%i/" % self.id
	def get_delete_url(self):
		return "/delete/list/%i/" % self.id	
	def get_add_url(self):
		return "/add/list/"
	def get_map_url(self):
		return "/map/list/%i/" % self.id
#may want to add something to the course set to record status, where status could be "Active", "Inactive" or "Complete"		

#stores the course detail (organisms in a course)
class CourseDetail(models.Model):
	course = models.ForeignKey(Course, related_name="course_details")
	organism = models.ForeignKey(Organism)

# **************************************************************** #
# ********************** user settings *************************** #
# **************************************************************** #

#stores show/hide status and home zipcode for a user
class UserSettings(models.Model):
	user = models.ForeignKey(User, related_name="+")
	hide_trees = models.BooleanField()
	hide_birds = models.BooleanField()
	hide_reptiles = models.BooleanField()
	hide_amphibians = models.BooleanField()
	hide_mammals = models.BooleanField()
	zipcode = models.ForeignKey(ZipCode, null=True, default=None, blank=True)
	private = models.BooleanField()
	class Meta:
		verbose_name_plural = "user settings"
	def get_absolute_url(self):
		return "/accounts/profile/%i/" % self.id
	def get_edit_url(self):
		return "/accounts/profile/%i/edit/" % self.id

# **************************************************************** #
# *********************** moderation ***************************** #
# **************************************************************** #	

# moderation.register(OrgIdentification)
# moderation.register(IdentificationDetail)	