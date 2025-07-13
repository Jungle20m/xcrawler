from uuid import UUID
from typing import TypedDict, List
from pymongo import MongoClient
from pymongo.collection import Collection
from bson import Binary
import uuid


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

    def insert_post(self, post: Post) -> None:
        collection = self.db["posts"]
        collection.insert_one(post)

    def insert_posts(self, posts: List[Post]) -> None:
        collection = self.db["posts"]
        collection.insert_many(posts)
