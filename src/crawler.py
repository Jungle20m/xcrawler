import time

from src.scraper.apify import ApiFy
from src.scraper import alphy
from src.db import DB, Post
from src import parser
from src.logger import get_logger

logger = get_logger()

class Crawler():
    def __init__(self):
        self.apify = ApiFy(token="", actor="")
        self.db = DB(connection_string="mongodb://admin:password@localhost:27017/")

    def run(self):
        # users = ["elonmusk", "realDonaldTrump"]     
        # data = self.apify.scrape_tweeter_data(users=users)
        
        # posts = parser.dicts_to_posts(data)
        # self.db.insert_posts(posts)


        users = [
            "BarackObama",
            "katyperry",
            "justinbieber",
            "rihanna",
            "taylorswift13",
            "Cristiano",
            "ladygaga",
            "TheEllenShow",
            "YouTube",
            "ArianaGrande",
            "realDonaldTrump",
            "jtimberlake",
            "KimKardashian",
            "selenagomez",
            "Twitter",
            "britneyspears",
            "cnnbrk",
            "narendramodi",
            "shakira",
            "jimmyfallon",
            "BillGates",
            "neymarjr",
            "nytimes",
            "MileyCyrus",
            "JLo",
            "KingJames",
            "CNN",
            "BrunoMars",
            "Oprah",
            "BBCBreaking",
            "iamsrk",
            "SrBachchan",
            "NiallOfficial",
            "Drake",
            "BeingSalmanKhan",
            "instagram",
            "SportsCenter",
            "KevinHart4real",
            "wizkhalifa",
            "espn",
            "LilTunechi",
            "NASA",
            "Harry_Styles",
            "Louis_Tomlinson",
            "realmadrid",
            "akshaykumar",
            "LiamPayne",
            "imVkohli",
            "Pink",
            "chrisbrown",
            "FCBarcelona",
            "PMOIndia",
            "sachin_rt",
            "onedirection",
            "elonmusk",
            "aliciakeys",
            "KylieJenner",
            "KAKA",
            "kanyewest",
            "EmmaWatson",
            "NBA",
            "ConanOBrien",
            "KendallJenner",
            "zaynmalik",
            "khloekardashian",
            "Adele",
            "POTUS",
            "iHrithik",
            "ActuallyNPH",
            "deepikapadukone",
            "BBCWorld",
            "HillaryClinton",
            "pitbull",
            "ChampionsLeague",
            "danieltosh",
            "priyankachopra",
            "aamir_khan",
            "NFL",
            "kourtneykardash",
            "MesutOzil1088",
            "andresiniesta8",
            "ShawnMendes",
            "TheEconomist",
            "coldplay",
            "NatGeo",
            "BTS_twt",
            "Eminem",
            "arrahman",
            "Google",
            "AvrilLavigne",
            "MariahCarey",
            "davidguetta",
            "Reuters",
            "premierleague",
            "ManUtd",
            "AnushkaSharma",
            "blakeshelton",
            "NICKIMINAJ",
            "ricky_martin",
            "MohamadAlarefe"
        ]    
        
        for user in users:
            try:
                logger.info(f"Scraping: {user}")

                data = alphy.scrape_tweet(user)
                posts = alphy.dicts_to_posts(data)
                self.db.insert_posts(posts)
                time.sleep(5)
                
                logger.info("Successful.")
            except Exception as e:
                logger.error(e)
    