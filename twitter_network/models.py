from django.db import models


class UserInfo(models.Model):
    screen_name = models.CharField(max_length=255)
    tweet_name = models.CharField(max_length=255)
    followings = models.IntegerField()
    followers = models.IntegerField()
    favorites_count = models.IntegerField()
    tweets_count = models.IntegerField()
    localisation = models.CharField(max_length=255)
    photo_profile = models.URLField(max_length=256,
                                    blank=True)
    profile_banner_url = models.URLField(max_length=256,
                                    blank=True)


class UserTweet(models.Model):
    screen_name = models.CharField(max_length=255)
    tweet_text = models.CharField(max_length=255)
