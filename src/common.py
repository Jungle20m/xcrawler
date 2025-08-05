from typing import Optional, List
from datetime import datetime

from dateutil import parser
from dateutil.tz import tzutc

from src.db import Post
from src.domain.browser import BrowserDomain


def parse_time(time_str: Optional[str]) -> Optional[datetime]:
    if not time_str:
        return None
    try:
        dt = parser.parse(time_str)
        return dt.astimezone(tzutc())
    except ValueError:
        return None


def dicts_to_posts(items: List[dict]) -> List[Post]:
    posts: List[Post] = []
    
    for item in items:
        # Tạo Post cho bài đăng chính
        ref_post_id = item.get("retweet", {}).get("id", "") if item.get("isRetweet", False) else ""
        post: Post = {
            "post_id": item.get("id"),
            "url": item.get("url"),
            "text": item.get("text"),
            "full_text": item.get("text"),
            "source": None,
            "retweet_count": item.get("retweetCount"),
            "reply_count": item.get("replyCount"),
            "like_count": item.get("likeCount"),
            "view_count": item.get("viewCount"),
            "quote_count": item.get("quoteCount"),
            "ref_post_id": ref_post_id,
            "is_retweet": item.get("isRetweet", False),
            "is_quote": None,
            "author_site_id": item.get("author", {}).get("id"),
            "created_at": parse_time(item.get("createdAt")),
            "media": item.get("media")
        }
        posts.append(post)
        
        # Nếu là retweet, tạo thêm Post cho bài retweet
        if item.get("isRetweet", False) and "retweet" in item:
            retweet = item["retweet"]
            retweet_post: Post = {
                "post_id": retweet.get("id"),
                "url": retweet.get("url"),
                "text": retweet.get("text"),
                "full_text": retweet.get("text"),
                "source": None,
                "retweet_count": retweet.get("retweetCount"),
                "reply_count": retweet.get("replyCount"),
                "like_count": retweet.get("likeCount"),
                "view_count": item.get("viewCount"),
                "quote_count": retweet.get("quoteCount"),
                "ref_post_id": retweet.get("quoteId"),
                "is_retweet": False,  # Bài retweet không được coi là retweet
                "is_quote": None,
                "author_site_id": retweet.get("author", {}).get("id"),
                "created_at": parse_time(retweet.get("createdAt")),
                "media": retweet.get("media")
            }
            posts.append(retweet_post)
    
    return posts


class BrowserSelector:
    def __init__(self, browsers: List[BrowserDomain]):
        self.browsers = browsers
        self.current_index = -1
        self.total_browsers = len(browsers)

    def get_browser(self) -> BrowserDomain:
        self.current_index = (self.current_index + 1) % self.total_browsers
        current_browser = self.browsers[self.current_index]
        return current_browser
    
    def get_browser_index(self) -> int:
        return self.current_index