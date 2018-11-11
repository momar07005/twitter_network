from django.db import models


class UserInfo(models.Model):
    screen_name = models.CharField(max_length=255)
    tweet_name = models.CharField(max_length=255)
    friends_number = models.IntegerField()
    followings = models.IntegerField()
    followers = models.IntegerField()
    localisation = models.CharField(max_length=255)
    photo_profile = models.URLField(max_length=256,
                                    db_index=True,
                                    unique=True,
                                    blank=True)
