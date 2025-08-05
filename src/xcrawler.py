import json
import time
import threading
import os
from typing import List

from kafka import KafkaProducer

from src.logger import Logger
from src.db import DB, Post, Author
from src.exception import ErrorForbidden, ErrorTooManyRequest
from src.xscraper import TwitterScraper
from src.common import dicts_to_posts, BrowserSelector
from src.domain.user import UserDomain
from src.domain.browser import BrowserDomain

    
logger = Logger() 

          
class PostCrawler:
    def __init__(self, num_workers: int, number_browser_per_thread: int = 1):
        self.db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
        # self.producer = KafkaProducer(
        #     bootstrap_servers='192.168.102.5:19092',
        #     value_serializer=lambda x: json.dumps(x).encode('utf-8')
        # )
        
        self.num_workers = num_workers
        self.number_browser_per_thread = number_browser_per_thread
        
        # Load profiles from file
        with open("data/browser_configs.json", 'r', encoding='utf-8') as file:
            browser_data = json.load(file)
        
        self.browsers = [BrowserDomain(user_agent=p["user_agent"], proxy=p["proxy"]) for p in browser_data]
        
        # Validate if we have enough profiles
        browsers_needed = self.num_workers * self.number_browser_per_thread
        if browsers_needed > len(self.browsers):
            raise ValueError(f"Not enough profiles! Need {browsers_needed}, but only have {len(self.browsers)}")
        
    def _scrape(self, thread_id, browser: List[BrowserDomain]):
        users = []
        user_file = f"data/users/{thread_id}.txt"
        with open(user_file, 'r', encoding='utf-8') as file:
            for line in file:
                parts = line.strip().split(',')
                if len(parts) >= 2:
                    name = parts[0]
                    id = parts[1]
                    user = {"name": name, "id": id}
                    users.append(user)
         
        browser_selector = BrowserSelector(browsers=browser)       
        browser = browser_selector.get_browser()
        
        scraper = TwitterScraper()
        headers = scraper.get_headers(browser=browser)
        
        for user in users:
            try:
                data = scraper.scrape_posts_by_user_id(user_id=user["id"], browser=browser, headers=headers)
                posts = dicts_to_posts(data)
                self.db.upsert_posts(posts)
                
                # TODO: to reduce the size of the data, we should compress the data before sending to kafka
                # consider using lz4, zstd, gzip, etc.
                # self.producer.send('twetter_posts', value=data)
                
                logger.info(f"[thread {thread_id}] - browser: {browser_selector.get_browser_index()} - user: {user["name"]}: success")
            except (ErrorTooManyRequest, ErrorForbidden) as e:
                # If the error is too many request or forbidden, 
                # we should update the browser config and re-new the headers
                logger.error(f"[thread {thread_id}] - browser: {browser_selector.get_browser_index()} - user: {user["name"]}: {e} -> update browser")
                browser = browser_selector.get_browser()
                headers = scraper.get_headers(browser=browser)
            except Exception as e:
                logger.error(f"[thread {thread_id}] - browser: {browser_selector.get_browser_index()} - user: {user["name"]}: {e}")
            finally:
                time.sleep(2)
        
    def run(self):
        # TODO: refactor this logic, it's so dumb
        # Divide profiles among threads
        if self.number_browser_per_thread:
            # Use specified profiles per thread
            threads = []
            start_idx = 0
            
            for thread_id in range(self.num_workers):
                end_idx = start_idx + self.number_browser_per_thread
                browsers = self.browsers[start_idx:end_idx]
                
                thread = threading.Thread(target=self._scrape, args=(thread_id, browsers), daemon=True)
                thread.start()
                threads.append(thread)
                
                start_idx = end_idx
        else:
            # Auto-distribute all profiles evenly
            browsers_per_thread = len(self.browsers) // self.num_workers
            remaining_profiles = len(self.browsers) % self.num_workers
            
            threads = []
            start_idx = 0
            
            for thread_id in range(self.num_workers):
                # Calculate number of profiles for this thread
                thread_profile_count = browsers_per_thread + (1 if thread_id < remaining_profiles else 0)
                end_idx = start_idx + thread_profile_count
                
                # Assign profiles to this thread
                browsers = self.browsers[start_idx:end_idx]
                
                thread = threading.Thread(target=self._scrape, args=(thread_id, browsers), daemon=True)
                thread.start()
                threads.append(thread)
                
                start_idx = end_idx
        
        for thread in threads:
            thread.join()
            
        self.producer.flush()
        self.producer.close()
        logger.info("All the threads are terminated!!!")
        
    
class HomeCrawler:
    def __init__(self):
        self.db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
        # self.producer = KafkaProducer(
        #     bootstrap_servers='192.168.102.5:19092',
        #     value_serializer=lambda x: json.dumps(x).encode('utf-8')
        # )
        
    def _scrape(self, users: List[UserDomain]):
        twitter = TwitterScraper()
        for user in users:
            try: 
                browser = self.db.get_browser_by_id(user.browser_id) 
                data = twitter.scrape_posts_from_home(user.cookie_file, browser)
                posts = dicts_to_posts(data)
                self.db.upsert_posts(posts)
                logger.info(f"scrape home - user: {user.screen_name} - success")
            except Exception as e:
                logger.error(f"scrape home - user: {user.screen_name} - {e}")
            finally:
                time.sleep(2)
    
    def run(self):
        # Get logged in users
        users = self.db.get_logged_in_users()
        self._scrape(users=users)