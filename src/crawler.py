import json
import time
import threading

from kafka import KafkaProducer

from src.logger import Logger
from src.scraper import alphy
from src.db import DB, Post, Author
from src.scraper.apify import ApiFy
from src.exception import ErrorForbidden, ErrorTooManyRequest
from src.scraper.alphy import AlphyExtractor, Profile, ProfileSelector

    
logger = Logger() 

          
class APICrawler:
    def __init__(self, num_workers: int, profiles_per_thread: int = None):
        self.num_workers = num_workers
        self.profiles_per_thread = profiles_per_thread
        self.db = DB(connection_string="mongodb://admin:password@192.168.102.5:27017/")
        self.producer = KafkaProducer(
            bootstrap_servers='192.168.102.5:19092',
            value_serializer=lambda x: json.dumps(x).encode('utf-8')
        )
        
        # Load profiles from file
        with open("data/profiles.json", 'r', encoding='utf-8') as file:
            profiles_data = json.load(file)
        
        self.profile_pool = [Profile(user_agent=p["user_agent"], proxy=p["proxy"]) for p in profiles_data]
        
        # Validate if we have enough profiles
        total_profiles_needed = self.num_workers * (self.profiles_per_thread or 1)
        if self.profiles_per_thread and total_profiles_needed > len(self.profile_pool):
            raise ValueError(f"Not enough profiles! Need {total_profiles_needed}, but only have {len(self.profile_pool)}")
        
    def _scrape(self, thread_id, assigned_profiles):
        profile_selector = ProfileSelector(assigned_profiles)
                
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
                
        extractor = AlphyExtractor(profile=profile_selector.get_profile())
        
        for user in users:
            try:
                data = extractor.scrape(user_id=user["id"])
                posts = alphy.dicts_to_posts(data)
                self.db.upsert_posts(posts)
                
                # TODO: to reduce the size of the data, we should compress the data before sending to kafka
                # consider using lz4, zstd, gzip, etc.
                # self.producer.send('twetter_posts', value=data)
                
                logger.info(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: success")
            except ErrorTooManyRequest as e:
                logger.error(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: {e}")
                logger.info(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - update new profile")
                extractor.refresh(profile=profile_selector.get_profile())
            except ErrorForbidden as e:
                logger.error(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: {e}")
                logger.info(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - update new profile")
                extractor.refresh(profile=profile_selector.get_profile())
            except Exception as e:
                logger.error(f"[thread {thread_id}] - profile: {profile_selector.get_profile_index()} - user: {user["name"]}: {e}")
            finally:
                time.sleep(2)
        
    def run(self):
        # Divide profiles among threads
        if self.profiles_per_thread:
            # Use specified profiles per thread
            threads = []
            start_idx = 0
            
            for thread_id in range(self.num_workers):
                end_idx = start_idx + self.profiles_per_thread
                assigned_profiles = self.profile_pool[start_idx:end_idx]
                
                thread = threading.Thread(target=self._scrape, args=(thread_id, assigned_profiles), daemon=True)
                thread.start()
                threads.append(thread)
                
                start_idx = end_idx
        else:
            # Auto-distribute all profiles evenly
            profiles_per_thread = len(self.profile_pool) // self.num_workers
            remaining_profiles = len(self.profile_pool) % self.num_workers
            
            threads = []
            start_idx = 0
            
            for thread_id in range(self.num_workers):
                # Calculate number of profiles for this thread
                thread_profile_count = profiles_per_thread + (1 if thread_id < remaining_profiles else 0)
                end_idx = start_idx + thread_profile_count
                
                # Assign profiles to this thread
                assigned_profiles = self.profile_pool[start_idx:end_idx]
                
                thread = threading.Thread(target=self._scrape, args=(thread_id, assigned_profiles), daemon=True)
                thread.start()
                threads.append(thread)
                
                start_idx = end_idx
        
        for thread in threads:
            thread.join()
            
        self.producer.flush()
        self.producer.close()
        logger.info("All the threads are terminated!!!")
            