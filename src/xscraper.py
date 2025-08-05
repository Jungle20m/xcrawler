import time
import json
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass

import requests
import jmespath
from dateutil import parser
from dateutil.tz import tzutc
from playwright.sync_api import sync_playwright, StorageState

from src.db import Post
from src.exception import ErrorHeaderNotFound, ErrorDataNotFound, ErrorTooManyRequest
from src.logger import Logger
from src.domain.browser import BrowserDomain
from src.domain.user import UserDomain

USER_TWEET_EXPRESSION = """
data.user.result.timeline.timeline.instructions[?type=='TimelineAddEntries'].entries[].content.itemContent.tweet_results.result.{
    id: legacy.id_str,
    url: core.user_results.result.core.screen_name != null && join('', ['https://x.com/', core.user_results.result.core.screen_name, '/status/', rest_id]),
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
        url: legacy.retweeted_status_result.result.core.user_results.result.core.screen_name != null && join('', ['https://x.com/', legacy.retweeted_status_result.result.core.user_results.result.core.screen_name, '/status/', legacy.retweeted_status_result.result.rest_id]),
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
        },
        media: legacy.retweeted_status_result.result.legacy.entities.media[] | [].{
            type: type,
            media_url_https: media_url_https,
            video_info: type == 'video' && {
                aspect_ratio: video_info.aspect_ratio,
                duration_millis: video_info.duration_millis,
                variants: video_info.variants
            } || null
        }
    } || null,
    author: {
        id: core.user_results.result.rest_id,
        userName: core.user_results.result.core.screen_name,
        name: core.user_results.result.core.name
    },
    media: legacy.entities.media[] | [].{
        type: type,
        media_url_https: media_url_https,
        video_info: type == 'video' && {
            aspect_ratio: video_info.aspect_ratio,
            duration_millis: video_info.duration_millis,
            variants: video_info.variants
        } || null
    }
}
"""


HOME_TWEET_EXPRESSION = """
data.home.home_timeline_urt.instructions[?type=='TimelineAddEntries'].entries[].content.itemContent.tweet_results.result.{
    id: legacy.id_str,
    url: core.user_results.result.core.screen_name != null && join('', ['https://x.com/', core.user_results.result.core.screen_name, '/status/', rest_id]),
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
        url: legacy.retweeted_status_result.result.core.user_results.result.core.screen_name != null && join('', ['https://x.com/', legacy.retweeted_status_result.result.core.user_results.result.core.screen_name, '/status/', legacy.retweeted_status_result.result.rest_id]),
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
        },
        media: legacy.retweeted_status_result.result.legacy.entities.media[] | [].{
            type: type,
            media_url_https: media_url_https,
            video_info: type == 'video' && {
                aspect_ratio: video_info.aspect_ratio,
                duration_millis: video_info.duration_millis,
                variants: video_info.variants
            } || null
        }
    } || null,
    author: {
        id: core.user_results.result.rest_id,
        userName: core.user_results.result.core.screen_name,
        name: core.user_results.result.core.name
    },
    media: legacy.entities.media[] | [].{
        type: type,
        media_url_https: media_url_https,
        video_info: type == 'video' && {
            aspect_ratio: video_info.aspect_ratio,
            duration_millis: video_info.duration_millis,
            variants: video_info.variants
        } || null
    }
}
"""

logger = Logger()

class TwitterScraper:
    def __init__(self):
        pass
        
    def __get_from_browser(self, browser: BrowserDomain) -> (str, dict):
        if browser is None:
            return None, None
        
        if browser.proxy is None:
            return browser.user_agent, None

        return browser.user_agent, {
            "server": f"{browser.proxy['host']}:{browser.proxy['port']}",
            "username": browser.proxy['username'],
            "password": browser.proxy['password']
        }
    
    def get_headers(self, browser: BrowserDomain) -> dict:
        _xhr_calls = []
        
        def intercept_request(request):
            if request.resource_type == "xhr":
                print(request.url)
                _xhr_calls.append(request)
            return request

        def wait_for_headers(timeout=30000):
            start_time = time.time()
            while time.time() - start_time < timeout / 1000:
                for xhr in _xhr_calls:
                    if "Viewer" in xhr.url:
                        return xhr.headers
                time.sleep(0.1)
            return None
        
        with sync_playwright() as pw:
            try: 
                url = "https://x.com/"              
                chrome = pw.chromium.launch(headless=False)
                user_agent, proxy = self.__get_from_browser(browser)
                context = chrome.new_context(
                    viewport={"width": 1920, "height": 1080}, 
                    user_agent=user_agent,
                    proxy=proxy
                )
                page = context.new_page()

                page.on("request", intercept_request)
                page.goto(url, timeout=60000)
            
                cookies = context.cookies()
                cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
                                
                headers = wait_for_headers(timeout=30000)
                
                if headers is None:
                    raise ErrorHeaderNotFound
                    
                headers["Cookies"] = cookie_string
                return headers
            except Exception as e:
                raise e
    
    def scrape_posts_by_user_id(self, user_id: str, browser: BrowserDomain, headers: Dict):
        try:
            url = f"https://api.x.com/graphql/4cddsYq56gFfTNDAljwNOw/UserTweets?variables=%7B%22userId%22%3A%22{user_id}%22%2C%22count%22%3A20%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%7D&features=%7B%22rweb_video_screen_enabled%22%3Afalse%2C%22payments_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22premium_content_api_read_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22responsive_web_grok_analyze_button_fetch_trends_enabled%22%3Afalse%2C%22responsive_web_grok_analyze_post_followups_enabled%22%3Afalse%2C%22responsive_web_jetfuel_frame%22%3Atrue%2C%22responsive_web_grok_share_attachment_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22responsive_web_grok_show_grok_translated_post%22%3Afalse%2C%22responsive_web_grok_analysis_button_from_backend%22%3Atrue%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_grok_image_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_community_note_auto_translation_is_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D&fieldToggles=%7B%22withArticlePlainText%22%3Afalse%7D"
            payload = {}
            response = requests.get(url, headers=headers, data=payload)
            response.raise_for_status()               
            data = jmespath.search(USER_TWEET_EXPRESSION, response.json())
            if data is None:
                raise ErrorDataNotFound
            return data
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise ErrorTooManyRequest
            raise
        except Exception as e:
            raise
    
    def login(self, user: UserDomain, browser: Optional[BrowserDomain] = None):
        with sync_playwright() as pw:
            try: 
                chrome = pw.chromium.launch(headless=False)
                user_agent, proxy = self.__get_from_browser(browser=browser)
                context = chrome.new_context(
                    viewport={"width": 1920, "height": 1080},
                    user_agent=user_agent,
                    proxy=proxy
                )
                page = context.new_page()

                page.goto("https://x.com/i/flow/login", timeout=120000)
                                
                time.sleep(120)
                
                return context.storage_state(path=user.cookie_file)
            except Exception as e:
                raise Exception(f"Error logging in: {e}")
            finally:
                chrome.close()
        
    def scrape_posts_from_home(self, state_file: str, browser: Optional[BrowserDomain] = None):
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
                    print(xhr.url)
                    if "HomeTimeline" in xhr.url: # check if the "UserTweets" is being called?
                        return xhr
                time.sleep(0.1)
            raise TimeoutError("Timeout waiting for HomeTimeline response")
        
        with sync_playwright() as pw:
            try: 
                chrome = pw.chromium.launch(headless=False)
                user_agent, proxy = self.__get_from_browser(browser=browser)
                context = chrome.new_context(
                    viewport={"width": 1920, "height": 1080}, 
                    storage_state=state_file,
                    user_agent=user_agent,
                    proxy=proxy
                )
                
                # Tạo trang mới
                page = context.new_page()
                page.on("response", intercept_response)
                page.goto("https://x.com/home")
                
                # go to url and wait for the page to load
                page.wait_for_selector("[data-testid='tweet']")
                
                response = wait_for_user_tweets(page, timeout=30000)
                data = jmespath.search(HOME_TWEET_EXPRESSION, response.json())
                if data is None:
                    raise ErrorDataNotFound
                return data
            except Exception as e:
                print(e)
            finally:
                chrome.close()