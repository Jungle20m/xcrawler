from apify_client import ApifyClient
from typing import List
import json


# class TwitterPost:
#     def __init__(self):
#         self.id: str = None
#         self.url: str = None
#         self.text: str = None
#         self.full_text: str = None
#         self.source: str = None
#         self.retweet_count: int = None
#         self.reply_count: int = None
#         self.like_count: int = None
#         self.quote_count: int = None

#     @classmethod
#     def from_json(cls, json_data: dict) -> 'TwitterPost':
#         post = cls()
#         post.id = json_data.get('id')
#         post.url = json_data.get('url')
#         post.text = json_data.get('text')
#         post.full_text = json_data.get('fullText')
#         post.source = json_data.get('source')
#         post.retweet_count = json_data.get('retweetCount')
#         post.reply_count = json_data.get('replyCount')
#         post.like_count = json_data.get('likeCount')
#         return post
    
    
#     def __str__(self) -> str:
#         data = {
#             'id': self.id,
#             'url': self.url,
#             'text': self.text,
#             'fullText': self.full_text,
#             'source': self.source,
#             'retweetCount': self.retweet_count,
#             'replyCount': self.reply_count
#         }
#         return json.dumps(data, indent=2, ensure_ascii=False)
    

class ApiFy():
    def __init__(self, token: str, actor: str):
        self.client = ApifyClient(token)
        self.twitter_actor = self.client.actor(actor)
        
    
    def scrape_tweeter_data(self, users: List[str]) -> List[dict]:
        input = {
            "author": "apify",
            "customMapFunction": "(object) => { return {...object} }",
            "end": "2021-07-02",
            "geocode": "37.7764685,-122.4172004,10km",
            "geotaggedNear": "Los Angeles",
            "inReplyTo": "webexpo",
            "includeSearchTerms": False,
            "maxItems": 4,
            "mentioning": "elonmusk",
            "minimumFavorites": 5,
            "minimumReplies": 5,
            "minimumRetweets": 5,
            "onlyImage": False,
            "onlyQuote": False,
            "onlyTwitterBlue": False,
            "onlyVerifiedUsers": False,
            "onlyVideo": False,
            "placeObjectId": "96683cc9126741d1",
            "sort": "Latest",
            "start": "2021-07-01",
            "tweetLanguage": "en",
            "twitterHandles": users,
            "withinRadius": "15km",
        }
        result = self.twitter_actor.call(run_input=input)
        if result is None:
            print('Actor run failed.')
            return []
    
        # Fetch results from the Actor run's default dataset.
        dataset_client = self.client.dataset(result['defaultDatasetId'])
        list_items_result = dataset_client.list_items()
        
        data = []
        for item in list_items_result.items:
            data.append(item)
            
        return data