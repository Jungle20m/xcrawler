from src.xcrawler import PostCrawler, HomeCrawler

      
if __name__ == '__main__':
    # crawler = PostCrawler(num_workers=1, number_browser_config_per_thread=10)
    # crawler.run()
  
    crawler = HomeCrawler(num_workers=1)
    crawler.run()
    
    