from datetime import datetime
from src.db import DB, Post, Media  # Giả sử class DB được lưu trong file db.py

def run_test():
    # Kết nối tới database test
    db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
    
    # Dữ liệu mẫu
    sample_post_1 = Post(
        post_id="1",
        url="http://example.com/post1",
        text="Original text 1",
        full_text="Original full text 1",
        source="web",
        retweet_count=10,
        reply_count=5,
        like_count=100,
        view_count=1000,
        quote_count=2,
        ref_post_id="ref1",
        is_retweet=False,
        is_quote=False,
        author_site_id="author1",
        created_at=datetime(2025, 7, 22),
        media=[Media(type="photo", media_url_https="http://media.com/1.jpg", video_info=None)]
    )

    sample_post_2 = Post(
        post_id="2",
        url="http://example.com/post2",
        text="Original text 2",
        full_text="Original full text 2",
        source="mobile",
        retweet_count=20,
        reply_count=10,
        like_count=200,
        view_count=2000,
        quote_count=4,
        ref_post_id="ref2",
        is_retweet=True,
        is_quote=False,
        author_site_id="author2",
        created_at=datetime(2025, 7, 22),
        media=[Media(type="video", media_url_https="http://media.com/2.mp4", video_info={"duration": 30})]
    )
    
    db.insert_posts([sample_post_1, sample_post_2])
    
     # Post cập nhật cho post_id="1"
    updated_post_1 = Post(
        post_id="1",
        url="http://example.com/post1",  # Không thay đổi
        text="Updated text 1",
        full_text="Updated full text 1",
        source="web",  # Không thay đổi
        retweet_count=15,
        reply_count=8,
        like_count=150,
        view_count=1500,
        quote_count=3,
        ref_post_id="ref1",  # Không thay đổi
        is_retweet=False,  # Không thay đổi
        is_quote=False,  # Không thay đổi
        author_site_id="author1",  # Không thay đổi
        created_at=datetime(2025, 6, 22),  # Không thay đổi
        media=[Media(type="photo", media_url_https="http://media.com/updated.jpg", video_info=None)]
    )
    
    new_post = Post(
        post_id="3",
        url="http://example.com/post3",
        text="New text 3",
        full_text="New full text 3",
        source="web",
        retweet_count=5,
        reply_count=2,
        like_count=50,
        view_count=500,
        quote_count=1,
        ref_post_id="ref3",
        is_retweet=False,
        is_quote=True,
        author_site_id="author3",
        created_at=datetime(2025, 7, 22),
        media=[]
    )
    
    db.upsert_posts([updated_post_1, new_post])
    