import time
import threading

from src.scraper.apify import ApiFy
from src.scraper import alphy
from src.scraper.alphy import AlphyExtractor
from src.db import DB, Post, Author
from src.logger import get_logger

logger = get_logger()

class Crawler():
    def __init__(self):
        self.apify = ApiFy(token="", actor="")
        self.db = DB(connection_string="mongodb://admin:password@localhost:27017/")

    def run(self):
        # users = ["elonmusk", "realDonaldTrump"]     
        # data = self.apify.scrape_tweeter_data(users=users)
        # posts = parser.dicts_to_posts(data)
        # self.db.insert_posts(posts)


        # users = ["elonmusk", "realDonaldTrump"]
        # for user in users:
        #     try:
        #         data = alphy.scrape_tweet(user)
        #         posts = alphy.dicts_to_posts(data)
        #         self.db.insert_posts(posts)
        #         time.sleep(5)                
        #     except Exception as e:
        #         logger.error(e)
        
        authors = self.db.get_authors()
        cookies = alphy.get_cookies(url="https://x.com")
        for author in authors:
            try:
                print(f"User: {author['name']}")                
                resp = alphy.get_user_tweets_without_auth(author["site_id"], user_name=author["name"], cookies=cookies)
                if resp != None:
                    posts = alphy.dicts_to_posts(resp)
                    self.db.insert_posts(posts)
                    print("successfully")
                
                
                time.sleep(6)
                    
            except Exception as e:
                print(e)
        
        
        # cookies = alphy.get_cookies(url="https://x.com")    
        # resp = alphy.get_user_tweets_without_auth(user_id="25073877", user_name="realDonaldTrump", cookies=cookies)
        # if resp != None:
        #     posts = alphy.dicts_to_posts(resp)
        #     self.db.insert_posts(posts)
        #     time.sleep(5)
        
        # with open("data/users.txt", 'r') as file:
        #     users = [line.strip() for line in file if line.strip()]    
        #     for user in users:
        #         rest_id = alphy.get_user_by_screen_name(user)
        #         if rest_id != None:
        #             print(rest_id)
        #             author = Author(name=user, site_id=rest_id)
        #             self.db.insert_author(author)
        #             time.sleep(1)
        
                    
class APICrawler:
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        
    def _scrape(self, thread_id: int):
        # Tạo profile cho chrome
        extractor = AlphyExtractor()
        # data = extractor.scrape(user_id="44196397")
        # print(data)
        
        
    def run(self):
        threads = []
        
        for id in range(self.num_workers):
            thread = threading.Thread(target=self._scrape, args=(id,), daemon=True)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()