import time
import threading

from src.scraper.apify import ApiFy
from src.scraper import alphy
from src.scraper.alphy import AlphyExtractor, Profile, ProfileSelector
from src.db import DB, Post, Author
from src.logger import Logger
from src.exception import ErrorTooManyRequest

    
    
logger = Logger() 



              
                    
class APICrawler:
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        self.db = DB(connection_string="mongodb://admin:password@192.168.1.143:27017/")
        
    def _scrape(self, thread_id):
        profiles_data = [
            {
                "user_agent": None,
                "proxy": None
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
                "proxy": {"server": "http://38.154.227.167:5868", "username": "zrgsinee", "password": "3lgguwj49847"}
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
                "proxy": {"server": "http://107.172.163.27:6543", "username": "zrgsinee", "password": "3lgguwj49847"}
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.2420.81",
                "proxy": {"server": "http://23.95.150.145:6114", "username": "zrgsinee", "password": "3lgguwj49847"}
            },
            {
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 OPR/109.0.0.0",
                "proxy": {"server": "http://198.23.239.134:6540", "username": "zrgsinee", "password": "3lgguwj49847"}
            }
        ]
        profiles = [Profile(user_agent=p["user_agent"], proxy=p["proxy"]) for p in profiles_data]
        profile_selector = ProfileSelector(profiles)
                
        users = []
        with open("data/users/users_1000.txt", 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    name = parts[0]
                    id = parts[1]
                    user = {"name": name, "id": id}
                    users.append(user)
                
        extractor = AlphyExtractor(profile=profile_selector.get_profile())
        
        for user in users:
            try:
                data = extractor.scrape(user_id=user["id"])
                posts = alphy.dicts_to_posts(data)
                self.db.upsert_posts(posts)
                
                logger.info(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: success")
            except ErrorTooManyRequest as e:
                logger.error(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: {e}")
                logger.info(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - update new profile")
                extractor.refresh(profile=profile_selector.get_profile())
            except Exception as e:
                logger.error(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: {e}")
            finally:
                time.sleep(2)
        
    def run(self):
        threads = []
        for thread_id in range(self.num_workers):
            thread = threading.Thread(target=self._scrape, args=(thread_id,), daemon=True)
            thread.start()
            threads.append(thread)
        
        for thread in threads:
            thread.join()
            
        logger.info("All the threads are terminated!!!")
            