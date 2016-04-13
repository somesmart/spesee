from django.db import models
from django.core.urlresolvers import reverse
import datetime
from django.contrib.auth.models import User
import os
from imagekit.models import ImageSpecField
from imagekit.processors import ResizeToFill, Adjust
import tagging
from tagging.fields import TagField
from tagging.models import Tag
from tagging.registry import register

# *********************************************************************** #
# **************************set up/meta data **************************** #
# *********************************************************************** #

def get_image_path(instance, filename):
	return os.path.join('photos/organism', str(instance.organism.id), filename)

#where the different types of organisms (Bird, Tree, Amphibian) are stored
class OrganismType(models.Model):
	description = models.CharField(max_length=200)
	def __unicode__(self):
		return self.description

class TypeTag(models.Model):
	tag = models.ForeignKey(Tag)
	type = models.ForeignKey(OrganismType)

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

# ****************************************************************** #
# ********************* organism/detail data *********************** #
# ****************************************************************** #

class Organism(models.Model):
	common_name = models.CharField(max_length=200)
	latin_name = models.CharField(max_length=200)
	population_status = models.ForeignKey(PopulationStatus, related_name="org_pop_status", null=True, default=None, blank=True)
	family = models.ForeignKey(Family, related_name="org_family", null=True, default=None, blank=True)
	order = models.ForeignKey(Order, related_name="org_order", null=True, default=None, blank=True)
	sp_class = models.ForeignKey(Sp_Class, related_name="org_class", null=True, default=None, blank=True)
	phylum = models.ForeignKey(Phylum, related_name="org_phylum", null=True, default=None, blank=True)
	kingdom = models.ForeignKey(Kingdom, related_name="org_kingdom", null=True, default=None, blank=True)
	type = models.ForeignKey(OrganismType, related_name="organisms")
	#ident_tips = models.TextField('identification tips', blank=True) no longer needed
	#habitat_descr = models.TextField('habitat description', blank=True) no longer needed
	#image = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True) no longer needed

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
	organism = models.OneToOneField(Organism, related_name='org_ident')
	identification = models.TextField(blank=True)
	#may want to add "last edit date, last edit user, etc"?
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
	description = models.CharField(max_length=250) #Don't need this anymore
	def __unicode__(self):
		return u"%s is %s" % (self.field.name, self.description)
	#consider doing a def save here to store the description slugified...
	class Meta:
		verbose_name_plural = "identification details"

register(Organism)

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
	thumbnail = ImageSpecField(source='observation_image', processors=[ResizeToFill(50, 50)], format='JPEG', options={'quality': 90})
	large_image = ImageSpecField(source='observation_image', processors=[ResizeToFill(500, 400)], format='JPEG', options={'quality': 90})
	wide_thumb = ImageSpecField(source='observation_image', processors=[ResizeToFill(200, 100)], format='JPEG', options={'quality': 90})
	def __unicode__(self):
		return self.location_descr
	def __unicode__(self):
		return self.comments	

#stores the unknown observation so others can review it later
class ObservationUnknown(models.Model):
	STATUS_CHOICES = (
        (1, 'Identified'),
        (2, 'Pending'),
        (3, 'Unknown'),
    )
	organism = models.ForeignKey(Organism, null=True, default=None, blank=True)
	user = models.TextField(blank=True)
	observation_date = models.DateTimeField()
	temperature = models.DecimalField(max_digits=5, decimal_places=2)
	latitude = models.DecimalField(max_digits=11, decimal_places=9)
	longitude = models.DecimalField(max_digits=11, decimal_places=9)
	location_descr = models.CharField('description of location', max_length=200)
	comments = models.CharField(max_length=200)
	quantity = models.IntegerField()
	observation_image = models.ImageField(upload_to='photos/%Y/%m/%d', blank=True)
	modified_by = models.ForeignKey(User, related_name='+')
	modified_date = models.DateTimeField()
	status = models.IntegerField(choices=STATUS_CHOICES) #1 - Approved; 2 - Pending; 3 - Rejected
	reason = models.TextField(blank=True)
	moderated_by = models.ForeignKey(User, related_name='+', null=True, default=None, blank=True)
	moderated_date = models.DateTimeField(null=True, default=None, blank=True)
	def __unicode__(self):
		return self.comments

class Images(models.Model):
	STATUS_CHOICES = (
        (1, 'Approved'),
        (2, 'Pending'),
        (3, 'Rejected'),
    )
	org_image = models.ImageField(upload_to=get_image_path, blank=True)
	thumbnail = ImageSpecField(source='org_image', processors=[ResizeToFill(50, 50)], format='JPEG', options={'quality': 90})
	large_image = ImageSpecField(source='org_image', processors=[ResizeToFill(500, 400)], format='JPEG', options={'quality': 90})
	wide_thumb = ImageSpecField(source='org_image', processors=[ResizeToFill(200, 100)], format='JPEG', options={'quality': 90})
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