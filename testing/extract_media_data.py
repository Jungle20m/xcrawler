import jmespath
import json
from src.scraper.alphy import dicts_to_posts



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


def run():
    
    with open("data/content/content_with_video.json", 'r') as file:
        data = json.load(file)

    result = jmespath.search(TWEET_EXPRESSION, data)
    posts = dicts_to_posts(result)
    
    for post in posts[:3]:
        print(post)