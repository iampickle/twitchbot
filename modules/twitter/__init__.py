import os
import tweepy
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

auth = tweepy.OAuthHandler(str(os.getenv('consumer-key')), str(os.getenv('consumer-secret')))
auth.set_access_token(os.getenv('access-token'), os.getenv('access-token-secret'))
api = tweepy.API(auth)
api2 = tweepy.Client(bearer_token=os.getenv('bearer-token'),
                    access_token=os.getenv('access-token'),
                    access_token_secret=os.getenv('access-token-secret'),
                    consumer_key=str(os.getenv('consumer-key')),
                    consumer_secret=str(os.getenv('consumer-secret')))

def tweet_text(text):
        try:
            api2.create_tweet(text=text)
            print('tweeted:\n'+text)
        except Exception as e:
            print('error while tweeting', e)

def tweet_pics(paths, text=""):
    try:
        media_ids = []
        for path in paths:
            resp = api.media_upload(path)
            media_ids.append(resp.media_id_string)
        
        api2.create_tweet(text=text, media_ids=media_ids)
        print('Tweeted pictures!')
    except Exception as e:
        print('Error while tweeting', e)
        
def tweet_media(path, text=""):
    try:
        resp = api.media_upload(path, media_category='tweet_video')
        print(resp.media_id_string)
        api2.create_tweet(text=text, media_ids=[str(resp.media_id_string)])
    except Exception as e:
        print('error while tweeting', e)
        print(resp)