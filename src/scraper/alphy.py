import time
from typing import List, Optional, Dict
from datetime import datetime
from dataclasses import dataclass

import requests
import jmespath
from dateutil import parser
from dateutil.tz import tzutc
from playwright.sync_api import sync_playwright

from src.db import Post
from src.exception import ErrorHeaderNotFound, ErrorDataNotFound, ErrorTooManyRequest


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
        
        
def get_cookies(url) -> str:
    with sync_playwright() as p:
        # Khởi tạo trình duyệt (có thể chọn 'chromium', 'firefox', hoặc 'webkit')
        browser = p.chromium.launch(headless=True)  # headless=True để chạy không giao diện
        context = browser.new_context()

        # Mở một trang mới
        page = context.new_page()

        # Điều hướng đến website
        page.goto(url)

        # Lấy tất cả cookie
        cookies = context.cookies()

        # Đóng trình duyệt
        browser.close()
        
        cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
       
        # Trả về danh sách cookie
        return cookie_string
    
    
def get_user_tweets_without_auth(user_id: str, user_name: str, cookies: str):
    # URL với userId được thay thế động
    url = f"https://api.x.com/graphql/4cddsYq56gFfTNDAljwNOw/UserTweets?variables=%7B%22userId%22%3A%22{user_id}%22%2C%22count%22%3A20%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%7D&features=%7B%22rweb_video_screen_enabled%22%3Afalse%2C%22payments_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22premium_content_api_read_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22responsive_web_grok_analyze_button_fetch_trends_enabled%22%3Afalse%2C%22responsive_web_grok_analyze_post_followups_enabled%22%3Afalse%2C%22responsive_web_jetfuel_frame%22%3Atrue%2C%22responsive_web_grok_share_attachment_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22responsive_web_grok_show_grok_translated_post%22%3Afalse%2C%22responsive_web_grok_analysis_button_from_backend%22%3Atrue%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_grok_image_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_community_note_auto_translation_is_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D&fieldToggles=%7B%22withArticlePlainText%22%3Afalse%7D"
    
    # Headers với cookie được truyền vào
    headers = {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'content-type': 'application/json',
        'origin': 'https://x.com',
        'priority': 'u=1, i',
        'referer': 'https://x.com/',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-site',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-client-transaction-id': 'rt2nLZyJn54d4wvVgc4dzUDlKSsdyh5jNP5CoTlo9O1ntJDavcOJnX0Oldd8jD4oPSNhiKp4anCF4i2/8uag3JxgaHoBrQ',
        'x-guest-token': '1945054484276896183',
        'x-twitter-active-user': 'yes',
        'x-twitter-client-language': 'vi',
        'x-xp-forwarded-for': '188df199e9582eadc7bd22932971f88b379135ccac9cbacd1fdc61dbe2daedda34b95bca0680722b96a078a339b25573524fcc31d41d797d84f57a08e87c07919d1f92d1caaff3ebc85d242ec005c36fb12944161050377508c283e9d1fbf25b4696d4b0c708f3fdc1d3496ef073410927551497446760b34c30eeb227efc82f996eab2f59afa28f4c94bf86d836b44d48d27ca4a865550d14fb9b129922c37c612eb145d0eda9925c13dc52f81317682958908c625cd1d8cf6968080590c4fcf88967ab02a9e0155ad056e1e06613d3484dea82a0657092b3ce0c068e3f160504a8937780ab46bc2c2f749d5a534a71d199faa5adf0fc6f59ff3258f2db23dc5d',
        'Cookie': cookies
    }

    payload = {}

    try:
        response = requests.get(url, headers=headers, data=payload)
        response.raise_for_status()  # Ném ngoại lệ nếu có lỗi HTTP (4xx, 5xx)
        
        data = jmespath.search(TWEET_EXPRESSION, response.json())
        return data  # Trả về đối tượng JSON
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except requests.exceptions.JSONDecodeError as json_err:
        print(f"JSON decode error occurred: {json_err}")
        return None
    except requests.exceptions.RequestException as req_err:
        print(f"Request error occurred: {req_err}")
        return None
    

def get_user_by_screen_name(screen_name: str) -> str:
    url = f"https://x.com/i/api/graphql/1F38Jtjett-7b8eQKstioA/UserByScreenName?variables=%7B%22screen_name%22%3A%22{screen_name}%22%7D&features=%7B%22responsive_web_grok_bio_auto_translation_is_enabled%22%3Afalse%2C%22hidden_profile_subscriptions_enabled%22%3Atrue%2C%22payments_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22subscriptions_verification_info_is_identity_verified_enabled%22%3Atrue%2C%22subscriptions_verification_info_verified_since_enabled%22%3Atrue%2C%22highlights_tweets_tab_ui_enabled%22%3Atrue%2C%22responsive_web_twitter_article_notes_tab_enabled%22%3Atrue%2C%22subscriptions_feature_can_gift_premium%22%3Atrue%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%7D&fieldToggles=%7B%22withAuxiliaryUserLabels%22%3Atrue%7D"

    # Headers giống như trong code của bạn
    headers = {
        'accept': '*/*',
        'accept-language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
        'authorization': 'Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA',
        'content-type': 'application/json',
        'priority': 'u=1, i',
        'referer': f'https://x.com/{screen_name}',
        'sec-ch-ua': '"Not)A;Brand";v="8", "Chromium";v="138", "Google Chrome";v="138"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'x-client-transaction-id': 'y+AIPXpBh/y6d9FNXWJ+K26hgTFzi8U+DBwBbMY6ttlHqLZn0IKs5S5gRxgh1GohBHkI7c/rUpprDHbIXo5m3xMLO5SeyA',
        'x-csrf-token': '84794c0340ff3557f905d47f1b7bcbbd14873caddaf64d6215fd0f91dc29c75b8e8b7014a0ed37b799ac525eba27058361c6c4783a40dd6dcd15aaf768e564246fc1e4ca59e790e3766833b71bbfa9a5',
        'x-twitter-active-user': 'yes',
        'x-twitter-auth-type': 'OAuth2Session',
        'x-twitter-client-language': 'en',
        'x-xp-forwarded-for': '90d243f0e07749eca7593a6d533f8bab778a1dfe5bf985a1dc955bd55e175165c8c356aec4702df5a49b5361b558c117c0e89be6498396c4ce7c6faa71b5304b82383a571e1a1f9507696c2144d4ad1f60238f83e1374df474fdcc27f02b7c1c8b410a280bed61300e40ebd6cc1559bfa85a35436d6f67dcbc09a9f809689eeb8825545ce19ade1458fe8c2e4dc60ecd06d8265365f769a71c12f6482bc56afdfd9ea5d0895fbc0e18011c8b9fee2830e4ba57833b3973a4f6104e72aaf9e4553670fe390373e8ee1e868b31785168657bbebd008dc3f7c905f5dcc142e9e531677501316bb8f19c6b644040e4c502e6ad0b4ef513720381e0644db2102a73004c',
        'Cookie': 'guest_id_marketing=v1%3A175232920821022242; guest_id_ads=v1%3A175232920821022242; guest_id=v1%3A175232920821022242; personalization_id="v1_5MA8wNpXOWV/lzNSTry1iQ=="; g_state={"i_l":0}; kdt=PmiqtcPSwcNt68vIgui5jMFhhRP9xxMtNMUBe8eE; auth_token=b0b86f134e998645fe99d2317f6aa2bb1aaca707; ct0=84794c0340ff3557f905d47f1b7bcbbd14873caddaf64d6215fd0f91dc29c75b8e8b7014a0ed37b799ac525eba27058361c6c4783a40dd6dcd15aaf768e564246fc1e4ca59e790e3766833b71bbfa9a5; twid=u%3D1942252032146219008; _ga=GA1.1.1709319368.1752363902; ph_phc_TXdpocbGVeZVm5VJmAsHTMrCofBQu3e0kN8HGMNGTVW_posthog=%7B%22distinct_id%22%3A%220197ff48-6703-727f-a8d4-d74c7193508c%22%2C%22%24sesid%22%3A%5B1752365045163%2C%2201980107-2867-740d-8fdd-b233959da50f%22%2C1752363903079%5D%7D; _ga_RJGMY4G45L=GS2.1.s1752363902$o1$g0$t1752365092$j60$l0$h0; lang=en; __cf_bm=OeS2GJ83ciJFljlWinjs7yIn5siRKLDooEi1qnerbR0-1752573625-1.0.1.1-KUc9xz5aYAvgEEtAK7bWm_mbbDK113_gXL_mGGbf3.4OdmWHEHcnaRdtxzB0GHl1tUwrKb0lbmSlaV4.XrY.2InWcBep17J6t1Hnsj6CoqY; guest_id=v1%3A175241826122169330; guest_id_ads=v1%3A175241826122169330; guest_id_marketing=v1%3A175241826122169330; personalization_id="v1_C5eOKH3ZDs/XDaKVkxiQ+g=="'
    }

    try:
        response = requests.get(url, headers=headers)

        # Kiểm tra nếu request thành công
        if response.status_code == 200:
            data = response.json()
            # Lấy rest_id từ response
            rest_id = data.get("data", {}).get("user", {}).get("result", {}).get("rest_id", None)
            if rest_id:
                return rest_id
            else:
                print("khong tim thay rest_id")
                return None
        else:
            print(f"response status != 200: {response.status_code}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"error: {e}")
        return None


@dataclass
class Profile:
    user_agent: Optional[str] = None
    proxy: Optional[Dict] = None
    

class ProfileSelector:
    def __init__(self, profiles: List[Profile]):
        self.profiles = profiles
        self.current_index = -1
        self.total_profiles = len(profiles)

    def get_profile(self) -> Profile:
        self.current_index = (self.current_index + 1) % self.total_profiles
        current_profile = self.profiles[self.current_index]
        return current_profile
    
    def get_profile_index(self) -> int:
        return self.current_index
    

class AlphyExtractor:
    def __init__(self, profile: Profile):
        self.user_agent = profile.user_agent
        self.proxy = profile.proxy
        self.headers = self._get_headers()
    
    
    def _get_headers(self) -> dict:
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
                browser = pw.chromium.launch(proxy=self.proxy, headless=False)
                context = browser.new_context(viewport={"width": 1920, "height": 1080}, user_agent=self.user_agent)
                page = context.new_page()

                page.on("request", intercept_request)
                page.goto(url)
            
                cookies = context.cookies()
                cookie_string = "; ".join([f"{cookie['name']}={cookie['value']}" for cookie in cookies])
                                
                headers = wait_for_headers(timeout=30000)
                
                if headers is None:
                    raise ErrorHeaderNotFound
                    
                headers["Cookies"] = cookie_string
                return headers
            except Exception as e:
                raise e
    
    
    def refresh(self, profile: Profile):
        self.user_agent = profile.user_agent
        self.proxy = profile.proxy
        self.headers = self._get_headers()
    
        
    def scrape(self, user_id: str):
        try:
            url = f"https://api.x.com/graphql/4cddsYq56gFfTNDAljwNOw/UserTweets?variables=%7B%22userId%22%3A%22{user_id}%22%2C%22count%22%3A20%2C%22includePromotedContent%22%3Atrue%2C%22withQuickPromoteEligibilityTweetFields%22%3Atrue%2C%22withVoice%22%3Atrue%7D&features=%7B%22rweb_video_screen_enabled%22%3Afalse%2C%22payments_enabled%22%3Afalse%2C%22profile_label_improvements_pcf_label_in_post_enabled%22%3Atrue%2C%22rweb_tipjar_consumption_enabled%22%3Atrue%2C%22verified_phone_label_enabled%22%3Afalse%2C%22creator_subscriptions_tweet_preview_api_enabled%22%3Atrue%2C%22responsive_web_graphql_timeline_navigation_enabled%22%3Atrue%2C%22responsive_web_graphql_skip_user_profile_image_extensions_enabled%22%3Afalse%2C%22premium_content_api_read_enabled%22%3Afalse%2C%22communities_web_enable_tweet_community_results_fetch%22%3Atrue%2C%22c9s_tweet_anatomy_moderator_badge_enabled%22%3Atrue%2C%22responsive_web_grok_analyze_button_fetch_trends_enabled%22%3Afalse%2C%22responsive_web_grok_analyze_post_followups_enabled%22%3Afalse%2C%22responsive_web_jetfuel_frame%22%3Atrue%2C%22responsive_web_grok_share_attachment_enabled%22%3Atrue%2C%22articles_preview_enabled%22%3Atrue%2C%22responsive_web_edit_tweet_api_enabled%22%3Atrue%2C%22graphql_is_translatable_rweb_tweet_is_translatable_enabled%22%3Atrue%2C%22view_counts_everywhere_api_enabled%22%3Atrue%2C%22longform_notetweets_consumption_enabled%22%3Atrue%2C%22responsive_web_twitter_article_tweet_consumption_enabled%22%3Atrue%2C%22tweet_awards_web_tipping_enabled%22%3Afalse%2C%22responsive_web_grok_show_grok_translated_post%22%3Afalse%2C%22responsive_web_grok_analysis_button_from_backend%22%3Atrue%2C%22creator_subscriptions_quote_tweet_preview_enabled%22%3Afalse%2C%22freedom_of_speech_not_reach_fetch_enabled%22%3Atrue%2C%22standardized_nudges_misinfo%22%3Atrue%2C%22tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled%22%3Atrue%2C%22longform_notetweets_rich_text_read_enabled%22%3Atrue%2C%22longform_notetweets_inline_media_enabled%22%3Atrue%2C%22responsive_web_grok_image_annotation_enabled%22%3Atrue%2C%22responsive_web_grok_community_note_auto_translation_is_enabled%22%3Afalse%2C%22responsive_web_enhance_cards_enabled%22%3Afalse%7D&fieldToggles=%7B%22withArticlePlainText%22%3Afalse%7D"
            payload = {}
            response = requests.get(url, headers=self.headers, data=payload)
            response.raise_for_status()               
            data = jmespath.search(TWEET_EXPRESSION, response.json())
            if data is None:
                raise ErrorDataNotFound
            return data
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:
                raise ErrorTooManyRequest
            raise
        except Exception as e:
            raise
        