from src.crawler import APICrawler
      
if __name__ == '__main__':
    # Create crawler with 2 threads, 2 profiles per thread
    crawler = APICrawler(num_workers=10, profiles_per_thread=10)
    crawler.run()
