import time
from typing import List

import jmespath
from playwright.sync_api import sync_playwright

from src.db import Post


TWEET_EXPRESSION = """
data.user.result.timeline.timeline.instructions[?type=='TimelineAddEntries'].entries[].content.itemContent.tweet_results.result.{
    id: legacy.id_str,
    url: join('', ['https://x.com/', core.user_results.result.core.screen_name, '/status/', rest_id]),
    text: legacy.full_text,
    retweetCount: legacy.retweet_count,
    replyCount: legacy.reply_count,
    likeCount: legacy.favorite_count,
    quoteCount: legacy.quote_count,
    viewCount: views.count,
    createdAt: legacy.created_at,
    lang: legacy.lang,
    bookmarkCount: legacy.bookmark_count,
    isRetweet: legacy.retweeted_status_result != null
    retweet: legacy.retweeted_status_result.result != null && {
        id: legacy.retweeted_status_result.result.legacy.id_str,
        url: join('', ['https://x.com/', legacy.retweeted_status_result.result.core.user_results.result.core.screen_name, '/status/', legacy.retweeted_status_result.result.rest_id]),
        text: legacy.retweeted_status_result.result.legacy.full_text,
        retweetCount: legacy.retweeted_status_result.result.legacy.retweet_count,
        replyCount: legacy.retweeted_status_result.result.legacy.reply_count,
        likeCount: legacy.retweeted_status_result.result.legacy.favorite_count,
        quoteCount: legacy.retweeted_status_result.result.legacy.quote_count,
        viewCount: legacy.retweeted_status_result.result.views.count,
        createdAt: legacy.retweeted_status_result.result.legacy.created_at,
        lang: legacy.retweeted_status_result.result.legacy.lang,
        bookmarkCount: legacy.retweeted_status_result.result.legacy.bookmark_count,
        isRetweet: legacy.retweeted_status_result.result.legacy.retweeted_status_result != null,
        author: {
            id: legacy.retweeted_status_result.result.core.user_results.result.rest_id,
            userName: legacy.retweeted_status_result.result.core.user_results.result.core.screen_name,
            name: legacy.retweeted_status_result.result.core.user_results.result.core.name
        } 
    } || null,
    author: {
        id: core.user_results.result.rest_id,
        userName: core.user_results.result.core.screen_name,
        name: core.user_results.result.core.name
    } 
}
""" 


def scrape_tweet(user: str) -> dict:
    """
    Scrape a single tweet page for Tweet thread e.g.:
    https://twitter.com/Scrapfly_dev/status/1667013143904567296
    Return parent tweet, reply tweets and recommended tweets
    """
    _xhr_calls = []

    def intercept_response(response):
        """capture all background requests and save them"""
        # we can extract details from background requests
        if response.request.resource_type == "xhr":
            _xhr_calls.append(response)
        return response
    
    def wait_for_user_tweets(page, timeout=30000):
        """Wait until a UserTweets request has a response"""
        start_time = time.time()
        while time.time() - start_time < timeout / 1000:
            for xhr in _xhr_calls:
                if "UserTweets" in xhr.url: # check if the "UserTweets" is being called?
                    return xhr
            time.sleep(0.1)
        raise TimeoutError("Timeout waiting for UserTweets response")

    with sync_playwright() as pw:
        try: 
            url = "https://x.com/" + user                   
            browser = pw.chromium.launch(headless=False)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            # enable background request intercepting:
            page.on("response", intercept_response)
            # go to url and wait for the page to load
            page.goto(url)
            page.wait_for_selector("[data-testid='tweet']")

            response = wait_for_user_tweets(page, timeout=30000)
            
            # Apply expression to extract core data
            data = jmespath.search(TWEET_EXPRESSION, response.json())
            
            
            
            return data
        except Exception as e:
            
            return {}
        
        
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
            "author_site_id": item.get("author", {}).get("id")
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
                "author_site_id": retweet.get("author", {}).get("id")
            }
            posts.append(retweet_post)
    
    return posts