from src.crawler import APICrawler

# from testing import scrape_home

      
if __name__ == '__main__':
    # scrape_home.run()
    crawler = APICrawler(num_workers=10, profiles_per_thread=10)
    crawler.run()
  