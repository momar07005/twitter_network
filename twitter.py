
# coding: utf-8




#Import librairies

import tweepy
import csv
import pandas as pd
import time
import sys
import json

import requests
from requests_oauthlib import OAuth1




# login to Twitter API 

def login():
    
    CONSUMER_KEY = "ltjPz1qv9zq32qA2qHN2Oypxb"
    CONSUMER_SECRET = "RcIrQx9nkLj23HpVcSXNh0nbHcyyOk0rSfC4Klde1e7GhcATz6"
    ACCESS_TOKEN = "1038381241836417024-6yKxd48G7VYWQGHYYn7PLzGIwCaZsq"
    ACCESS_TOKEN_SECRET = "3p9RJ2Eb8Rpos2qpVzTKyy8Os75TwqJXXPhTFW4hYuoCy"
    
    OAUTH_KEYS = {'consumer_key':CONSUMER_KEY, 'consumer_secret':CONSUMER_SECRET,'access_token_key':ACCESS_TOKEN, 'access_token_secret':ACCESS_TOKEN_SECRET}

    auth = tweepy.OAuthHandler(OAUTH_KEYS['consumer_key'], OAUTH_KEYS['consumer_secret'])

    twitter_api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True)
    
    # Authentification twitter API provided by Twitter

    auth = OAuth1(CONSUMER_KEY, CONSUMER_SECRET, ACCESS_TOKEN, ACCESS_TOKEN_SECRET)

    
    sys.stdout.write(" Connected ...")

    return twitter_api, auth


# Do search with a keyword
def twitter_search(twitter_api, keyword, max_results=200):
    
    search = tweepy.Cursor(twitter_api.search, q=keyword).items(max_results)
    
    return search
    

# Save search result in a csv file
def save_in_csv(results_search):
    
    df = pd.DataFrame()
    
    user = [] # User who makes the tweet
    text = [] # Tweet content
    
    # We can add some additionals informations
    
    for tweet in results_search:
        user.append(tweet.user.screen_name)
        text.append(tweet.text)
        
    df['user'] = user
    df['text'] = text
    
    # Write out Tweets
    df.to_csv('user_tweet.csv',index = False,encoding='utf-8')
    
    print("---------------------- Well saved in user_tweet.csv ----------------------")
    
    return df
    


def generate_node(twitter_api, df):
    
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
        dfUsers = pd.concat([dfUsers,dfTemp])
        time.sleep(30) # avoids hitting Twitter rate limit
        # Progress bar to track approximate progress
        count +=1
        per = round(count*100.0/name_count,1)
        sys.stdout.write("\rTwitter call %s%% complete." % per)
        sys.stdout.flush()
        
    dfUsers["weight"] = 1
        
    return dfUsers
    
    


# Retrieve some additionnals informations for each user

def get_infos_node(df):
    
    # Create a list of the unique usernames in order to see which users we need to retrieve friends for.
    all_names = list(df['user'].unique())
    
    additional_information = dict()
    
    for name in all_names:
        source = twitter_api.get_user(screen_name='TL_Gendarmerie')
        additional_information[source.id] = [ source.screen_name , source.followers_count, source.friends_count ,
                                              source.location , source.profile_image_url ]
   
    additional_information = json.dumps(additional_information, indent=4)
    with open("node_infos.json", "w") as write_file:
        json.dump(additional_information, write_file)
    

def get_datas(q , max_result = 100):

    twitter_api, auth = login()


    search = twitter_search(twitter_api, q, max_result)


    df = save_in_csv(search)



    dfUsers = generate_node(twitter_api, df)


    # Again, to limit the number of calls to Twitter API, just do lookups on followers that connect to those in our user group.
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
                df.drop(df[mask].index[0],inplace=True)
        except:
            continue
            


    # For each user retrieve the 100 last fav

    root_url = 'https://api.twitter.com/1.1/favorites/list.json?count=100&screen_name='

    all_names = df["userFromName"].unique()

    i = 0

    for screen_name in all_names:
        
        url = root_url + screen_name

        rq = requests.get(url,auth=auth)

        data = rq.json()

        tempon = len(data)


        for x in range(tempon):

            if data[x]["user"]["id"] in list(df["userToId"]):

                mask = (df["userFromName"] == screen_name) & (df["userToId"] == data[x]["user"]["id"])

                if not df[mask].empty:
                    df.loc[df[mask].index[0], "weight"] += 2

        url = ''

        i  += 1
        sys.stdout.write("\r {0}. {1}".format(i,screen_name))
        sys.stdout.flush()
        time.sleep(5)
            

    df.to_csv('data_make_graph.csv', index=False, encoding='utf-8')

    print(" Youpi ! les données sont pretes ...")


