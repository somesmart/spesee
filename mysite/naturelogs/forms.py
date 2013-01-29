from django import forms
from django.forms import ModelForm, Textarea
from django.forms.models import inlineformset_factory
from mysite.nature.models import *
from registration.forms import RegistrationForm
from tagging.forms import TagField

# ****************************************************************** #
# ********************* organism related fms *********************** #
# ****************************************************************** #

class IdentificationDetailFormSet(forms.models.BaseInlineFormSet):
    def __init__(self, *args, **kwargs):
        super(IdentificationDetailFormSet, self).__init__(*args, **kwargs)
        for form in self.forms:
            self.update_choices(form)
    
    # We need to override the constructor (and the associated property) for the
    # empty form, so dynamic forms work.
    def _get_empty_form(self, **kwargs):
        form = super(IdentificationDetailFormSet, self)._get_empty_form(**kwargs)
        self.update_choices(form)
        return form
    empty_form = property(_get_empty_form)
    
    # This updates one form's 'field' field queryset, if there is an organism with type
    # associated with the formset. Otherwise, make the choice list empty.
    def update_choices(self, form):
        if 'type' in self.data:
            id_fields = OrganismType.objects.get(pk=self.data['type']).id_fields.all()
        elif self.instance.pk and self.instance.type:
            id_fields = self.instance.type.id_fields.all()
        else:
            id_fields = IdentificationDetail.objects.none()
        
        form.fields['field'].queryset = id_fields

class IdentificationDetailInline(forms.Form):
    model = IdentificationDetail
    formset = IdentificationDetailFormSet
    extra = 3
    tags = TagField() #do I need this tags stuff here?

    def save(self, commit=True):
        instance = super(IdentificationDetailInline, self).save(commit)
        instanct.tags = self.cleaned_data['tags']
        return instance

class ImagesForm(ModelForm):
    class Meta:
        model = Images
        caption = forms.CharField(required=False)
        exclude = ('organism', 'upload_user', 'upload_date', 'status', 'primary_image')

class OrgIdentReviewForm(ModelForm):
    class Meta:
        model = OrgIdentificationReview
        exclude = ('moderated_by', 'moderated_date', 'identification', 'organism', 'modified_by', 'modified_date')

class ImagesReviewForm(ModelForm):
    class Meta:
        model = ImagesReview
        exclude = ('moderated_by', 'moderated_date', 'review_image', 'modified_by', 'modified_date')        


IdentDetailFormSet = inlineformset_factory(Organism, IdentificationDetail, formset=IdentificationDetailFormSet, extra=3)        

ImagesFormSet = inlineformset_factory(Organism, Images, form=ImagesForm, extra=3)

# ****************************************************************** #
# ********************* observation related ************************ #
# ****************************************************************** #        

class ObservationForm(forms.ModelForm):
    class Meta:
        model = Observation
        exclude = ('user', 'organism', 'parent_observation')

class ObservationReviewForm(forms.ModelForm):
    class Meta:
        model = ObservationUnknown
        exclude = ('moderated_by', 'moderated_date', 'organism', 'modified_by', 'modified_date', 'user', 'observation_date', 'temperature', 'latitude', 'longitude', 'location_descr', 'comments', 'quantity', 'observation_image')

# ****************************************************************** #
# ********************* location related vws *********************** #
# ****************************************************************** #           

class LocationForm(forms.ModelForm):
    description = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': 70, 'rows': 10}))
    class Meta:
        model = Location
        exclude = ('created_by')

# ****************************************************************** #
# ********************* course related forms *********************** #
# ****************************************************************** #        

class CourseForm(ModelForm):
    course_descr = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
        
    class Meta:
        model = Course
        exclude = ('user', 'group')

    def __init__(self, *args, **kwargs):
        super(CourseForm, self).__init__(*args, **kwargs)
        self.fields['course_name'].label = "List Name"
        self.fields['course_descr'].label = "List Description"

class CourseDetailForm(ModelForm):
    class Meta:
        model = CourseDetail 

CourseDetailFormSet = inlineformset_factory(Course, CourseDetail, form=CourseDetailForm)

# ****************************************************************** #
# ********************* groups related forms *********************** #
# ****************************************************************** #        

class GroupForm(ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'size':'60'}))
        
    class Meta:
        model = Group
        exclude = ('owner')

# ****************************************************************** #
# ********************* user signup edit etc *********************** #
# ****************************************************************** #

class UserSettingsForm(forms.ModelForm):
    #hide_trees = forms.BooleanField(help_text='Check to Hide Trees')
    #hide_birds = forms.BooleanField(help_text='Check to Hide Birds')
    #hide_reptiles = forms.BooleanField(help_text='Check to Hide Reptiles')
    #hide_amphibians = forms.BooleanField(help_text='Check to Hide Amphibians')
    #hide_mammals = forms.BooleanField(help_text='Check to Hide Mammals')
    class Meta:
        model = UserSettings
        exclude = ('user', 'zipcode', 'private')

class UserRegistrationForm(RegistrationForm):
    hide_trees = forms.BooleanField(required=False, initial=False)
    hide_birds = forms.BooleanField(required=False, initial=False)
    hide_reptiles = forms.BooleanField(required=False, initial=False)
    hide_amphibians = forms.BooleanField(required=False, initial=False)
    hide_mammals = forms.BooleanField(required=False, initial=False)