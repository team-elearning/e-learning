from django.db import models
from django.contrib.postgres.fields import ArrayField

# Create your models here.
class Exploration(models.Model):
    # What this exploration is called.
    title = models.CharField(max_length=200)
    # The category this exploration belongs to.
    category = models.CharField(max_length=200, db_index = True, blank=False, null=False)
    # The objective of this exploration.
    objective = models.TextField(default='')
    # The ISO 639-1 code for the language this exploration is written in.
    language_code = models.CharField(max_length=10, default='en')
    # Tags (topics, skills, concepts, etc.) associated with this
    # exploration.
    tags = ArrayField(models.CharField(max_length=50), default=list, db_index = True)
    # The version of the exploration.
    version = models.IntegerField(default=1)
    