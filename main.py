from src.crawler import Crawler, APICrawler

      
if __name__ == '__main__':
    # crawler = Crawler()
    # crawler.run()
    
    crawler = APICrawler(num_workers=2)
    crawler.run()