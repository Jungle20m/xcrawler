from typing import TypedDict, List, Optional, Dict
from pymongo import MongoClient
from pymongo.operations import ReplaceOne, UpdateOne
from datetime import datetime


class Media(TypedDict):
    type: str
    media_url_https: str
    video_info: Optional[Dict]

class Post(TypedDict):
    post_id: str
    url: str
    text: str
    full_text: str
    source: str
    retweet_count: int
    reply_count: int
    like_count: int
    view_count: int
    quote_count: int
    ref_post_id: str
    is_retweet: bool
    is_quote: bool
    author_site_id: str
    created_at: datetime
    media: List[Media]
    
    
class Author(TypedDict):
    name: str
    url: str
    site_id: str
    followers: int
    following: int
    
    
class DB:
    def __init__(self, connection_string: str):
        self.client = MongoClient(connection_string)
        self.db = self.client["alphy"]
        self.author_collection = self.db["authors"]
        self.post_collection = self.db["posts"]

    def insert_post(self, post: Post) -> None:
        self.post_collection.insert_one(post)

    def insert_posts(self, posts: List[Post]) -> None:
        self.post_collection.insert_many(posts)
        
    def insert_author(self, author: Author) -> None:
        self.author_collection.insert_one(author)
        
    def get_authors(self) -> List[Author]:
        return list(self.author_collection.find())
    
    def upsert_posts(self, posts: List[Post]) -> None:
        operations = [
            UpdateOne(
                filter={"post_id": post["post_id"]},
                update={
                    "$set": {
                        "text": post["text"],
                        "full_text": post["full_text"],
                        "retweet_count": post["retweet_count"],
                        "reply_count": post["reply_count"],
                        "like_count": post["like_count"],
                        "view_count": post["view_count"],
                        "quote_count": post["quote_count"],
                        "media": post["media"]
                    },
                    "$setOnInsert": {
                        "post_id": post["post_id"],
                        "url": post["url"],
                        "source": post["source"],
                        "ref_post_id": post["ref_post_id"],
                        "is_retweet": post["is_retweet"],
                        "is_quote": post["is_quote"],
                        "author_site_id": post["author_site_id"],
                        "created_at": post["created_at"]
                    }
                },
                upsert=True
            ) for post in posts
        ]
        self.post_collection.bulk_write(operations, ordered=False)
