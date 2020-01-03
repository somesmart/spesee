from django_registration.signals import user_registered #user_activated
from nature.models import UserSettings
from nature.forms import UserRegistrationForm
from django.contrib.auth.models import Group

def create_profile(sender, user, request, **kwargs):
	form = UserRegistrationForm(request.POST)
	if 'hide_trees' in request.POST:
		hide_trees = form.data["hide_trees"]
	else:
		hide_trees = False
	if 'hide_birds' in request.POST:
		hide_birds = form.data["hide_birds"]
	else:
		hide_birds = False	
	if 'hide_reptiles' in request.POST:
		hide_reptiles = form.data["hide_reptiles"]
	else:
		hide_reptiles = False	
	if 'hide_amphibians' in request.POST:
		hide_amphibians = form.data["hide_amphibians"]
	else:
		hide_amphibians = False	
	if 'hide_mammals' in request.POST:
		hide_mammals = form.data["hide_mammals"]
	else:
		hide_mammals = False
	UserSettings(user=user, hide_trees=hide_trees, hide_birds=hide_birds, hide_reptiles=hide_reptiles, hide_amphibians=hide_amphibians, hide_mammals=hide_mammals, zipcode_id=form.data["zipcode"], private=False).save()
	#add the new user to the StandardUser group
	g = Group.objects.get(name="StandardUser")
	g.user_set.add(user)

user_registered.connect(create_profile)