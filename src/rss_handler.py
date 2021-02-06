import feedparser
from bs4 import BeautifulSoup as beau
import sqlite3 as sql
from datetime import datetime
import re


class RssHandler:
    def __init__(self, rss_url):
        self.db = "news2vid.db"
        self.db_con = sql.connect(self.db)
        self.db_cur = self.db_con.cursor()

        self.url = rss_url
        # self.feed_tails = {
        #     "top_stories": "top_stories/feed/",
        #     "gs": "gs/feed/",
        #     "business": "business/feed/",
        #     "entertainment": "entertainment/feed/",
        #     "health": "health/feed/",
        #     "sci-tech": "sci-tech/feed/",
        #     "daily": "daily_search_trends/feed/"
        # }
        self.rss_feeds = self.parse_rss_feed()

    # def __get_rss_feeds(self):
    #     rss_feeds = feedparser.parse(self.url)
    #     for cat, tail in self.feed_tails.items():
    #         rss_url = self.main_url + tail
    #         rss_feeds[cat] = feedparser.parse(rss_url)
    #     return rss_feeds

    @staticmethod
    def __check_news_date(news_date):
        now = datetime.now()
        news_date = datetime.strptime(news_date, "%a, %d %b %Y %H:%M:%S %z")
        return now.day == news_date.day

    def parse_rss_feed(self):
        raw_feeds = feedparser.parse(self.url)
        parsed_feed = {}
        # for feed in raw_feeds.values():
        for entry in raw_feeds.entries:
            news_id = entry.id.split("p=")[-1]  # sample id from feedparser https://nl.trendnews.eu/?p=5077
            if self.__check_new_news(news_id):
                pass
            elif not self.__check_news_date(entry.published):
                pass
            else:
                news = parsed_feed[news_id] = {}
                news["url"] = entry.link
                news["title"] = entry.title
                # todo make this selectable among summary & content
                news["content"] = self.__parse_news(entry.summary)
        return parsed_feed

    @staticmethod
    def __split_news(news_txt):  # ensures any word in the news is intact
        txt_length = len(news_txt)
        quota = 5000  # google tts quota https://cloud.google.com/text-to-speech/quotas
        if txt_length < quota:
            return news_txt
        else:
            sentence_list = news_txt.split(".")
            part_quantity = len(range(0, txt_length, quota))
            parts = {i: [] for i in range(part_quantity)}
            part_length = 0
            counter = 0
            for sentence in sentence_list:
                sentence_length = len(sentence) + 1
                part_length += sentence_length
                if part_length >= quota:
                    part_length = 0
                    counter += 1
                parts[counter].append(sentence)
            for part_id, part in parts.items():
                parts[part_id] = ".".join(parts[part_id])
            return parts

    def __parse_news(self, rss_html_content: str):
        content = {}
        soup = beau(rss_html_content, "html.parser")

        # clean the last line
        soup.find_all("p")[-1].decompose()
        print("rss_Handler")
        img_url = re.split("(-)\d+(x)\d*", soup.find("img").attrs["src"])
        content["img_url"] = img_url[0] + img_url[-1].split("?")[0]
        txt = soup.text.rstrip()
        content["txt"] = self.__split_news(txt)
        return content

    def __check_new_news(self, news_id):
        query = bool(self.db_cur.execute(f"select * from main where news_id == '{news_id}'").fetchone())
        if not query:
            timestamp = datetime.timestamp(datetime.now())
            self.db_cur.execute(f"insert into main(news_id, timestamp) values ('{news_id}', {timestamp})")
            self.db_con.commit()
        return False  # todo change this and other stuff

