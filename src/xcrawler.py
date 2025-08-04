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
from src.common import dicts_to_posts
from src.profile import BrowserConfig, BrowserConfigSelector, UserProfile

    
logger = Logger() 

          
class PostCrawler:
    def __init__(self, num_workers: int, number_browser_config_per_thread: int = 1):
        self.num_workers = num_workers
        self.number_browser_config_per_thread = number_browser_config_per_thread
        self.db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
        self.producer = KafkaProducer(
            bootstrap_servers='192.168.102.5:19092',
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Load profiles from file
        with open("data/browser_configs.json", 'r', encoding='utf-8') as file:
            browser_config_data = json.load(file)
        
        self.browser_config_pool = [BrowserConfig(user_agent=p["user_agent"], proxy=p["proxy"]) for p in browser_config_data]
        
        # Validate if we have enough profiles
        total_browser_config_needed = self.num_workers * self.number_browser_config_per_thread
        if total_browser_config_needed > len(self.browser_config_pool):
            raise ValueError(f"Not enough profiles! Need {total_browser_config_needed}, but only have {len(self.browser_config_pool)}")
        
    def _scrape(self, thread_id, browser_configs: List[BrowserConfig]):
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
         
        browser_config_selector = BrowserConfigSelector(browser_configs=browser_configs)       
        browser_config = browser_config_selector.get_browser_config()
        
        scraper = TwitterScraper()
        headers = scraper.get_headers(config=browser_config)
        
        for user in users:
            try:
                data = scraper.scrape_posts_by_user_id(user_id=user["id"], config=browser_config, headers=headers)
                posts = dicts_to_posts(data)
                self.db.upsert_posts(posts)
                
                # TODO: to reduce the size of the data, we should compress the data before sending to kafka
                # consider using lz4, zstd, gzip, etc.
                # self.producer.send('twetter_posts', value=data)
                
                logger.info(f"[thread {thread_id}] - browser_config: {browser_config_selector.get_browser_config_index()} - user: {user["name"]}: success")
            except (ErrorTooManyRequest, ErrorForbidden) as e:
                # If the error is too many request or forbidden, 
                # we should update the browser config and re-new the headers
                logger.error(f"[thread {thread_id}] - browser_config: {browser_config_selector.get_browser_config_index()} - user: {user["name"]}: {e}")
                logger.info(f"[thread {thread_id}]- update browser config")
                browser_config = browser_config_selector.get_browser_config()
                headers = scraper.get_headers(browser_config)
            except Exception as e:
                logger.error(f"[thread {thread_id}] - browser_config: {browser_config_selector.get_browser_config_index()} - user: {user["name"]}: {e}")
            finally:
                time.sleep(2)
        
    def run(self):
        # Divide profiles among threads
        if self.number_browser_config_per_thread:
            # Use specified profiles per thread
            threads = []
            start_idx = 0
            
            for thread_id in range(self.num_workers):
                end_idx = start_idx + self.number_browser_config_per_thread
                browser_configs = self.browser_config_pool[start_idx:end_idx]
                
                thread = threading.Thread(target=self._scrape, args=(thread_id, browser_configs), daemon=True)
                thread.start()
                threads.append(thread)
                
                start_idx = end_idx
        else:
            # Auto-distribute all profiles evenly
            browser_configs_per_thread = len(self.browser_config_pool) // self.num_workers
            remaining_profiles = len(self.browser_config_pool) % self.num_workers
            
            threads = []
            start_idx = 0
            
            for thread_id in range(self.num_workers):
                # Calculate number of profiles for this thread
                thread_profile_count = browser_configs_per_thread + (1 if thread_id < remaining_profiles else 0)
                end_idx = start_idx + thread_profile_count
                
                # Assign profiles to this thread
                browser_configs = self.browser_config_pool[start_idx:end_idx]
                
                thread = threading.Thread(target=self._scrape, args=(thread_id, browser_configs), daemon=True)
                thread.start()
                threads.append(thread)
                
                start_idx = end_idx
        
        for thread in threads:
            thread.join()
            
        self.producer.flush()
        self.producer.close()
        logger.info("All the threads are terminated!!!")
        
    
class HomeCrawler:
    def __init__(self, num_workers: int):
        self.num_workers = num_workers
        # self.db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
        # self.producer = KafkaProducer(
        #     bootstrap_servers='192.168.102.5:19092',
        #     value_serializer=lambda x: json.dumps(x).encode('utf-8')
        # )
        
    def _scrape(self):
        def get_user(profile_folder: str) -> (UserProfile, BrowserConfig, bool):
            try:
                is_logined = False
                user_profile = None
                browser_config = None
                
                credential_file = f"{profile_folder}/credential.json"
                with open(credential_file, 'r', encoding='utf-8') as file:
                    credential = json.load(file)
                    user_profile = UserProfile(
                        email=credential.get("email"),
                        password=credential.get("password"),
                        screen_name=credential.get("screen_name"),
                        state_file=credential.get("state_file")
                    )
                    
                with open(user_profile.state_file, 'r', encoding='utf-8') as file:
                    state = json.load(file)
                    if state != {}:
                        is_logined = True
                    
                browser_config_file = f"{profile_folder}/browser_config.json"
                with open(browser_config_file, 'r', encoding='utf-8') as file:
                    browser_config = json.load(file)
                    browser_config = BrowserConfig(
                        user_agent=browser_config.get("user_agent"),
                        proxy=browser_config.get("proxy")
                    )
                
                return user_profile, browser_config, is_logined
            except Exception as e:
                logger.error(f"Error getting user profile: {e}")
                return None, None, False
        
        try:
            scraper = TwitterScraper()
            user_profile, browser_config, is_logined = get_user("data/user_profiles/1")
            
            if not is_logined:
                state = scraper.login(user_profile, browser_config)
                with open(user_profile.state_file, 'w', encoding='utf-8') as file:
                    json.dump(state, file)
            
            data = scraper.scrape_posts_from_home(user_profile.state_file, browser_config)
            posts = dicts_to_posts(data)
            print(posts)
            # self.db.upsert_posts(posts)
            # logger.info(f"Scraped {len(posts)} posts from home")
            
        except Exception as e:
            logger.error(f"Error scraping home: {e}")
        
    def run(self):
        self._scrape()