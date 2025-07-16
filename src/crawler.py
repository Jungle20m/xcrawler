import time
import threading

from src.scraper.apify import ApiFy
from src.scraper import alphy
from src.scraper.alphy import AlphyExtractor
from src.db import DB, Post, Author
from src.logger import Logger


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
    
    
logger = Logger()
              
              
                    
class APICrawler:
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
        
    def _scrape(self, thread_id, user_agent, proxy):
        users = []
        
        file_name = f"data/users/{thread_id}.txt"
        with open(file_name, 'r', encoding='utf-8') as file:
            for line in file:
                user = line.strip().split(',')[0]
                users.append(user)
                
        extractor = AlphyExtractor(
            user_agent=user_agent,
            proxy=proxy,
        )
        
        for user in users:
            try:
                data = extractor.scrape(user_id="44196397")
                posts = alphy.dicts_to_posts(data)
                self.db.insert_posts(posts)
                
                logger.info(f"[thread {thread_id}] user: {user}: success")
                time.sleep(6)
            except Exception as e:
                logger.error(f"[thread {thread_id}] user: {user}: {e}")
        
        
    def run(self):
        workers = [
            {
                "thread_id": "1",
                "user_agent": None,
                "proxy": None
            },
            {
                "thread_id": "2",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "proxy": {"server": "http://38.154.227.167:5868", "username": "zrgsinee", "password": "3lgguwj49847"}
            },
            {
                "thread_id": "3",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                "proxy": {"server": "http://92.113.242.158:6742", "username": "zrgsinee", "password": "3lgguwj49847"}
            },
            {
                "thread_id": "4",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
                "proxy": {"server": "http://23.95.150.145:6114", "username": "zrgsinee", "password": "3lgguwj49847"}
            },
            {
                "thread_id": "5",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
                "proxy": {"server": "http://198.23.239.134:6540", "username": "zrgsinee", "password": "3lgguwj49847"}
            }
        ]
        
        threads = []
        for worker in workers:
            thread = threading.Thread(target=self._scrape, args=(worker["thread_id"], worker["user_agent"], worker["proxy"]), daemon=True)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
            
        logger.info("All the threads are terminated!!!")
            