from django.db import models

# Create your models here.
class Collection(models.Model):
    # What this collection is called.
    title = models.CharField(max_length=255, required=True)
    # The category this collection belongs to.
    category = models.CharField(max_length=200, index = True, required = True)
    # The objective of this collection.
    objective = models.TextField(default='')
    # The language code of this collection.
    language_code = models.CharField(max_length=10, default='en')
    # Tags associated with this collection.
    tags = models.ArrayField(models.CharField(max_length=50), default=list, index = True)
    # A dict representing the contents of a collection. Currently, this
    # contains the list of nodes. This dict should contain collection data
    # whose structure might need to be changed in the future.
    Collection_contents = models.JSONField(default=dict) # e.g., {'nodes': [{'exploration_id': 'exp1'}, ...]}

    
