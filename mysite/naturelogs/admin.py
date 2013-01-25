from django.contrib import admin
from django.conf.urls.defaults import *
from django.http import HttpResponse

from mysite.nature.models import *
from mysite.nature.forms import IdentificationDetailFormSet
from tagging.forms import TagField
# from moderation.admin import ModerationAdmin

class IdentificationFieldInline(admin.TabularInline):
    model = IdentificationField
    extra = 3
    
class OrganismTypeAdmin(admin.ModelAdmin):
    inlines = [IdentificationFieldInline]
    
    # We want to expose a new URL, that gives us the available
    # choices when we change the OrganismType in an OrganismAdmin page.
    def get_urls(self, **kwargs):
        urls = super(OrganismTypeAdmin, self).get_urls(**kwargs)
        urls = patterns('', 
            url(r'^(.*)/fields/$', self.get_fields, name='organisms_organismtype_fields'),
        ) + urls
        return urls
    urls = property(get_urls)
    
    # This is a view method that returns an HTML fragment that can be used to
    # populate a <select> element.
    def get_fields(self, request, *args, **kwargs):
        data = "<option value>---------</option>"
        if args[0]:
            data += "".join([
                "<option value='%(id)s'>%(name)s</option>" % x 
                for x in OrganismType.objects.get(pk=args[0]).id_fields.values()
            ])
        return HttpResponse(data)


class IdentificationDetailInline(admin.TabularInline):
    model = IdentificationDetail
    formset = IdentificationDetailFormSet
    extra = 3
    tags = TagField()

    def save(self, commit=True):
        instance = super(IdentificationDetailInline, self).save(commit)
        instanct.tags = self.cleaned_data['tags']
        return instance

def latin_name(obj):
    return u"<i>%s</i>" % obj.latin_name
latin_name.allow_tags = True
latin_name.admin_order_field = 'latin_name'

class OrganismAdmin(admin.ModelAdmin):
    inlines = [IdentificationDetailInline]  
    list_display = (
        'common_name',
        latin_name,
        'type',
    )
    
    list_filter = ('type',)

class ObservationAdmin(admin.ModelAdmin):
    list_display = ('organism', 'observation_date', 'user', 'comments', 'quantity')
    list_filter = ('user',)

# class OrgIdentAdmin(ModerationAdmin):
#     pass

# admin.site.register(OrgIdentification, OrgIdentAdmin)
admin.site.register(OrganismType, OrganismTypeAdmin)
admin.site.register(Organism, OrganismAdmin)
admin.site.register(Observation, ObservationAdmin)
# admin.site.register(IdentificationField)
admin.site.register(TypeTag)
admin.site.register(Family)
admin.site.register(Order)
admin.site.register(Sp_Class)
admin.site.register(Phylum)
admin.site.register(Kingdom)
admin.site.register(PopulationStatus)
admin.site.register(Region)
admin.site.register(State)
admin.site.register(StateStatus)
admin.site.register(ZipCode)
# admin.site.register(IdentificationDetail)
admin.site.register(OrgRegion)
admin.site.register(OrgStateStatus)
admin.site.register(Course)
admin.site.register(CourseDetail)
#admin.site.register(CourseUsers)
admin.site.register(UserSettings)
admin.site.register(Images)
admin.site.register(Group)