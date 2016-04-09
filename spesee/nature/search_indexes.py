import datetime
from haystack import indexes
from nature.models import Organism, OrgIdentification

class OrgIdentificationIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    identification = indexes.CharField(model_attr='identification')
    content_auto = indexes.EdgeNgramField(model_attr='identification')

    def get_model(self):
        return OrgIdentification

class OrganismIndex(indexes.SearchIndex, indexes.Indexable):
	text = indexes.CharField(document=True, use_template=True)
	common_name = indexes.CharField(model_attr='common_name')
	latin_name = indexes.CharField(model_attr='latin_name')
	content_auto = indexes.EdgeNgramField(model_attr='common_name')

	def get_model(self):
		return Organism

		