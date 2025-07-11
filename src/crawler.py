from src.apify import ApiFy
from src.db import DB, Post
from src import parser

class Crawler():
    def __init__(self):
        self.apify = ApiFy(token="", actor="")
        self.db = DB(connection_string="mongodb://admin:password@localhost:27017/")

    def run(self):
        users = ["elonmusk", "realDonaldTrump"]     
        data = self.apify.scrape_tweeter_data(users=users)
        
        posts = parser.dicts_to_posts(data)
        self.db.insert_posts(posts)

    