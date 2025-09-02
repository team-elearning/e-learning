from django.db import models
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
class UserModel(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True, null=True)
    last_name = models.CharField(max_length=30, blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True)
    role = models.CharField(max_length=20, choices=[('student', 'Student'), ('instructor', 'Instructor'), ('admin', 'Admin')], default='student')
    phone = models.CharField(max_length=15, blank=True, null=True)

    def set_password(self, raw_password):  
        self.password = make_password(raw_password)
        self.save()
    
    def check_password(self, raw_password):
        return check_password(raw_password, self.password)

    def __str__(self):
        return self.email

# class CompletedActivity(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # IDs of all the explorations completed by the user.
#     exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Exploration IDs") 
#     # IDs of all the collections completed by the user.
#     collection_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Collection IDs")
#     # IDs of all the stories completed by the user.
#     story_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Story IDs")
#     # IDs of all the topics learnt by the user (i.e. the topics in which the
#     # learner has completed all the stories).
#     learnt_topic_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Learnt Topic IDs")
#     # IDs of all the topics learnt by the user(i.e. the topics in which the
#     # learner has completed all the subtopics).
#     mastery_topic_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Mastery Topic IDs")
    
# class IncompleteActivity(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # The ids of the explorations partially completed by the user.
#     exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Exploration IDs")
#     # The ids of the collections partially completed by the user.
#     collection_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Collection IDs")
#     # IDs of all the stories partially completed by the user.
#     story_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Story IDs")
#     # IDs of all the topics partially learnt by the user(i.e. the topics in
#     # which the learner has not completed all the stories).
#     partially_learnt_topic_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Partially Learnt Topic IDs")
#     # IDs of all the topics partially mastered by the user(i.e. the topics in
#     # which the learner has not completed all the subtopics).
#     partially_mastery_topic_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Partially Mastery Topic IDs")

# class ExpUserLastPlay(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     exploration_id = models.CharField(max_length=100)
#     # The version of the exploration last played by the user.
#     last_played_exp_version = models.IntegerField(default=None, blank=True, null=True)
#     # The name of the state at which the learner left the exploration when
#     # he/she last played it.
#     last_played_state_name = models.CharField(max_length=100, default=None, blank=True, null=True)


# class LearnerPlayList(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # IDs of all the explorations in the playlist of the user.
#     exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Exploration IDs")
#     # IDs of all the collections in the playlist of the user.
#     collection_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Collection IDs")


# class UserContributions(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # IDs of all the explorations created by the user.
#     created_exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Created Exploration IDs")
#     # IDs of explorations that this user has made a positive
#     # (i.e. non-revert) commit to.
#     edited_exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Edited Exploration IDs")
    

# class UserEmailPreferences(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # The user's preference for receiving general site updates. This is set to
#     # None if the user has never set a preference.
#     site_updates = models.BooleanField(default=None, null=True)
#     # The user's preference for receiving email when user is added as a member
#     # in exploration. This is set to True when user has never set a preference.
#     editor_role_notifications = models.BooleanField(default=None, null=True)
#     # The user's preference for receiving email when user receives feedback
#     # message for his/her exploration.
#     feedback_message_notifications = models.BooleanField(default=None, null=True)
#     # The user's preference for receiving email when a creator, to which this
#     # user has subscribed, publishes an exploration.
#     subscription_notifications = models.BooleanField(default=None, null=True)

# class UserSubscriptions(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # IDs of all the creators to whom the user has subscribed.
#     creator_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Creator IDs")
#     # IDs of explorations that this user subscribes to.
#     exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Exploration IDs")
#     # IDs of collections that this user subscribes to.
#     collection_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Collection IDs")
#     # IDs of feedback thread ids that this user subscribes to.
#     general_feedback_thread_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="General Feedback Thread IDs")
#     # When the user last checked notifications. May be None.
#     last_checked = models.DateTimeField(auto_now=True)

# class UserStats(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # The impact score
#     impact_score = models.FloatField(default=0.0)
#     # The total number of plays of all explorations by the user.
#     total_plays = models.IntegerField(default=0)
#     # The average ratings of all explorations by the user.
#     average_ratings = models.FloatField(default=0.0)
#     # The total number of ratings of all explorations by the user.
#     number_of_ratings = models.IntegerField(default=0)


# class ExplorationUserData(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     exploration_id = models.CharField(max_length=100)
#     # The rating (1-5) the user assigned to the exploration. Note that this
#     # represents a rating given on completion of the exploration.
#     rating = models.IntegerField(default=None, blank=True, null=True)


# class CollectionProgress(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     collection_id = models.CharField(max_length=100)
#     # The IDs of all the explorations completed by the user in this collection.
#     completed_exploration_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Completed Exploration IDs")


# class StoryProgress(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     story_id = models.CharField(max_length=100)
#     # The IDs of all the completed nodes in the story.
#     completed_node_ids = ArrayField(models.CharField(max_length=100), default=list, blank=True, null=True, verbose_name="Completed Node IDs")


# class UserQuery(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     query_id = models.CharField(max_length=100)
#     # Options for a query specified by query submitter.
#     # Query option to specify whether user has created or edited one or more
#     # explorations in last n days. This only returns users who have ever
#     # created or edited at least one exploration.
#     inactive_in_last_n_days = models.IntegerField(default=0)
#     # Query option to check whether given user has logged in
#     # since last n days.
#     has_not_logged_in_for_n_days = models.IntegerField(default=0)


# class UserSkillMastery(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     # The skill id for which the degree of mastery is stored.
#     skill_id = models.CharField(max_length=100)
#     # The degree of mastery of the skill by the user. This is a float value
#     # between 0 and 1 (inclusive).
#     mastery_level = models.FloatField(default=0.0)

