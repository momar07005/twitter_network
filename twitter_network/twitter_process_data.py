import tweepy
import pandas as pd
import time
import sys
import json

import requests
from requests_oauthlib import OAuth1

import os

from django.conf import settings as conf_settings

from twitter_network.models import UserTweet, UserInfo



# login to Twitter API
def login():
    
    CONSUMER_KEY = "21N9hZTYEhZxT43r2auEf99Xz"
    CONSUMER_SECRET = "uOzTAlvDaJoPvK4pPXLVWJMlpzotFrK5z8NF6BKrT7mTHFo0xW"
    ACCESS_TOKEN = "1038381241836417024-4wXcS9N703LV9qFlJ8FQVYgwoHNhDF"
    ACCESS_TOKEN_SECRET = "i15wlk1U6U46BP42e3C9qZuERemmOxurAnqFrqPOa7N55"
    
    OAUTH_KEYS = {'consumer_key':CONSUMER_KEY, 'consumer_secret':CONSUMER_SECRET,'access_token_key':ACCESS_TOKEN, 'access_token_secret':ACCESS_TOKEN_SECRET}

    auth = tweepy.OAuthHandler(OAUTH_KEYS['consumer_key'], OAUTH_KEYS['consumer_secret'])

    twitter_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    
    # Authentification twitter API provided by Twitter

    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    
    sys.stdout.write("********************* Twitter API Connected *********************\n")

    return twitter_api, auth


# Do search with a keyword
def twitter_search(twitter_api, keyword, max_results=200):
    
    search = tweepy.Cursor(twitter_api.search, q=keyword).items(max_results)
    
    return search
    

# Save search result in a csv file
def save_in_db(results_search):

    print("\nSaving tweets and owner ...")
    
    df = pd.DataFrame()
    
    user = [] # User who makes the tweet
    text = [] # Tweet content
    user_id = []
    
    # We can add some additionals informations
    
    for tweet in results_search:
        user.append(tweet.user.screen_name)
        text.append(tweet.text)
        user_id.append(tweet.user.id)
        user_tweet = tweet.user.screen_name
        user_text = tweet.text

        u = UserTweet(screen_name=user_tweet, tweet_text=user_text)

        u.save()

        print("User: {} saved !!!".format(user_tweet))
        
    df['user'] = user
    df['text'] = text
    df['user_id'] = user_id
    
    # Write out Tweets
    #df.to_csv('user_tweet.csv', index=False, encoding='utf-8')
    
    print("\n---------------------- Well saved  ----------------------")
    
    return df
    

def generate_node(twitter_api, df):

    print("\n\r ... Get data from Twitter  ...")
    
    # Create a list of the unique usernames in order to see which users we need to retrieve friends for.
    all_names = list(df['user'].unique())
    
    # Initialize dataframe of users that will hold the edge relationships
    dfUsers = pd.DataFrame()
    dfUsers['userFromName'] =[]
    dfUsers['userFromId'] =[]
    dfUsers['userToId'] = []
    count = 0
    
    name_count = len(all_names)
    # The choice to retrieve friends (who the user is following) rather than followers is intentional.
    # Either would work. However, many Twitter users follow fewer users than are following them, especially the most popular accounts. 
    # This reduces the number of very large calls to Twitter API, which seemed to cause problems.
    for name in all_names:
        # Build list of friends    
        currentFriends = []
        for page in tweepy.Cursor(twitter_api.friends_ids, screen_name=name).pages():
            currentFriends.extend(page)
        currentId = twitter_api.get_user(screen_name=name).id
        currentId = [currentId] * len(currentFriends)
        currentName = [name] * len(currentFriends)   
        dfTemp = pd.DataFrame()
        dfTemp['userFromName'] = currentName
        dfTemp['userFromId'] = currentId
        dfTemp['userToId'] = currentFriends
        dfUsers = pd.concat([dfUsers, dfTemp])
        time.sleep(30) # avoids hitting Twitter rate limit
        # Progress bar to track approximate progress
        count +=1
        per = round(count*100.0/name_count,1)
        sys.stdout.write("\rTwitter call %s%% complete." % per)
        sys.stdout.flush()
        
    dfUsers["weight"] = 1

    print("\n")
        
    return dfUsers
    

# Retrieve some additionnals informations for each user
def get_infos_node(twitter_api, df):
    
    # Create a list of the unique usernames in order to see which users we need to retrieve friends for.
    all_ids = list(df['user_id'].unique())

    
    for ids in all_ids:
        source = twitter_api.get_user(ids)

        screen_name = source.screen_name
        tweet_name = source.name
        followings = source.friends_count
        followers = source.followers_count
        localisation = source.location
        photo_profile = source.profile_image_url
        profile_banner_url = source.profile_banner_url
        favorites_count = source.favourites_count
        tweets_count = source.statuses_count


        u = UserInfo(screen_name=screen_name, tweet_name=tweet_name, followings=followings, followers=followers, favorites_count=favorites_count, tweets_count=tweets_count, localisation=localisation, photo_profile=photo_profile, profile_banner_url=profile_banner_url)
            
        u.save()


   

    

def get_data(q, max_result=100):

    twitter_api, auth = login()

    search = twitter_search(twitter_api, q, max_result)

    df = save_in_db(search)

    df_tempon = df

    dfUsers = generate_node(twitter_api, df)

    # Again, to limit the number of calls to Twitter API, just do lookups on followers that connect
    # to those in our user group.
    # We are not interested in "friends" that are not part of this community.
    fromId = dfUsers['userFromId'].unique()
    dfChat = dfUsers[dfUsers['userToId'].apply(lambda x: x in fromId)]

    # No more Twitter API lookups are necessary. Create a lookup table that we will use to get the verify the userToName
    dfLookup = dfChat[['userFromName','userFromId']]
    dfLookup = dfLookup.drop_duplicates()
    dfLookup.columns = ['userToName','userToId']
    dfCommunity = dfUsers.merge(dfLookup, on='userToId')
    dfCommunity.to_csv('dfCommunity.csv',index = False,encoding='utf-8')
    df = pd.read_csv('dfCommunity.csv')
    for x in range(len(df)):
        try:
            mask = (df["userFromName"] == df.iloc[x][3]) & (df["userToName"] == df.iloc[x][0])
            if not df[mask].empty:       
                df.drop(df[mask].index[0], inplace=True)
        except:
            continue

    # For each user retrieve the 100 last fav
    root_url = 'https://api.twitter.com/1.1/favorites/list.json?count=100&screen_name='
    all_names = df["userFromName"].unique()
    i = 0
    for screen_name in all_names:
        url = root_url + screen_name
        rq = requests.get(url, auth=auth)
        data = rq.json()
        tempon = len(data)
        for x in range(tempon):

            if data[x]["user"]["id"] in list(df["userToId"]):

                mask = (df["userFromName"] == screen_name) & (df["userToId"] == data[x]["user"]["id"])

                if not df[mask].empty:
                    df.loc[df[mask].index[0], "weight"] += 2

        url = ''

        i += 1
        print("\r {0}. {1}".format(i,screen_name))
        #sys.stdout.flush()
        time.sleep(5)
            
    df.to_csv(os.path.join(conf_settings.BASE_DIR, 'test_data.csv'), index=False, encoding='utf-8')

    get_infos_node(twitter_api, df_tempon)

    print(" Youpi ! les données sont pretes ...")






