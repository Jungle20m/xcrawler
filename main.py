from src.crawler import APICrawler
      
if __name__ == '__main__':
    crawler = APICrawler(num_workers=1)
    crawler.run()
