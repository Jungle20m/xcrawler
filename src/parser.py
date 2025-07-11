from typing import List
from src.db import Post


def dicts_to_posts(items: List[dict]) -> List[Post]:
    """
    Chuyển đổi danh sách dictionary từ API Twitter thành danh sách Post.
    Đối với bài đăng là retweet, tạo cả Post cho bài chính và bài retweet.
    
    :param items: Danh sách dictionary từ API Twitter.
    :return: Danh sách các Post (TypedDict).
    """
    posts: List[Post] = []
    
    for item in items:
        # Tạo Post cho bài đăng chính
        ref_post_id = item.get("retweet", {}).get("id", "") if item.get("isRetweet", False) else ""
        post: Post = {
            "post_id": item.get("id"),
            "url": item.get("url"),
            "text": item.get("text"),
            "full_text": item.get("fullText"),
            "source": item.get("source"),
            "retweet_count": item.get("retweetCount"),
            "reply_count": item.get("replyCount"),
            "like_count": item.get("likeCount"),
            "view_count": item.get("viewCount"),
            "quote_count": item.get("quoteCount"),
            "ref_post_id": ref_post_id,
            "is_retweet": item.get("isRetweet", False),
            "is_quote": item.get("isQuote", False),
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
                "full_text": retweet.get("fullText"),
                "source": retweet.get("source"),
                "retweet_count": retweet.get("retweetCount"),
                "reply_count": retweet.get("replyCount"),
                "like_count": retweet.get("likeCount"),
                "view_count": item.get("viewCount"),
                "quote_count": retweet.get("quoteCount"),
                "ref_post_id": retweet.get("quoteId"),
                "is_retweet": False,  # Bài retweet không được coi là retweet
                "is_quote": retweet.get("isQuote", False),
                "author_site_id": retweet.get("author", {}).get("id")
            }
            posts.append(retweet_post)
    
    return posts