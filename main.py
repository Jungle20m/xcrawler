import schedule
import time

from src.xcrawler import PostCrawler, HomeCrawler
      
def scrape_user_home():
    crawler = HomeCrawler()
    crawler.run()

def scrape_kol_posts():
    crawler = PostCrawler(num_workers=2, number_browser_per_thread=10)
    crawler.run()    
      
if __name__ == '__main__':
    schedule.every(2).minutes.do(scrape_user_home)
    schedule.every(2).minutes.do(scrape_kol_posts)
    
    print("start service...")
    while True:
        schedule.run_pending()
        time.sleep(2)
    
    
    