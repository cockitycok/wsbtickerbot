import re
import sys
import praw
import time
import json
import pprint
import operator
import datetime
import requests  # Para enviar logs a Discord
from praw.models import MoreComments
from iexfinance import Stock as IEXStock

# to add the path for Python to search for files to use my edited version of vaderSentiment
sys.path.insert(0, 'vaderSentiment/vaderSentiment')
from vaderSentiment import SentimentIntensityAnalyzer

# ---- CONFIGURA TU WEBHOOK AQUÍ ----
WEBHOOK_URL = "https://discord.com/api/webhooks/1434574084850843840/A0g7thttJeNJ2r0vXeFiJCXK3kkCkV_0ld6EUoxv185U3mz9DYI9fM9vT4845LoAsdK4"

def send_log_to_discord(message):
    data = {"content": message}
    try:
        response = requests.post(WEBHOOK_URL, json=data)
        if response.status_code != 204:
            print(f"Error enviando a Discord: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Excepción enviando a Discord: {e}")

def extract_ticker(body, start_index):
   count  = 0
   ticker = ""

   for char in body[start_index:]:
      if not char.isalpha():
         if (count == 0):
            return None
         return ticker.upper()
      else:
         ticker += char
         count += 1

   return ticker.upper()

def parse_section(ticker_dict, body):
   blacklist_words = [
      "YOLO", "TOS", "CEO", "CFO", "CTO", "DD", "BTFD", "WSB", "OK", "RH",
      "KYS", "FD", "TYS", "US", "USA", "IT", "ATH", "RIP", "BMW", "GDP",
      "OTM", "ATM", "ITM", "IMO", "LOL", "DOJ", "BE", "PR", "PC", "ICE",
      "TYS", "ISIS", "PRAY", "PT", "FBI", "SEC", "GOD", "NOT", "POS", "COD",
      "AYYMD", "FOMO", "TL;DR", "EDIT", "STILL", "LGMA", "WTF", "RAW", "PM",
      "LMAO", "LMFAO", "ROFL", "EZ", "RED", "BEZOS", "TICK", "IS", "DOW"
      "AM", "PM", "LPT", "GOAT", "FL", "CA", "IL", "PDFUA", "MACD", "HQ",
      "OP", "DJIA", "PS", "AH", "TL", "DR", "JAN", "FEB", "JUL", "AUG",
      "SEP", "SEPT", "OCT", "NOV", "DEC", "FDA", "IV", "ER", "IPO", "RISE"
      "IPA", "URL", "MILF", "BUT", "SSN", "FIFA", "USD", "CPU", "AT",
      "GG", "ELON"
   ]

   if '$' in body:
      index = body.find('$') + 1
      word = extract_ticker(body, index)
      
      if word and word not in blacklist_words:
         try:
            if word != "ROPE":
               price = IEXStock(word).get_price()
               if word in ticker_dict:
                  ticker_dict[word].count += 1
                  ticker_dict[word].bodies.append(body)
               else:
                  ticker_dict[word] = Ticker(word)
                  ticker_dict[word].count = 1
                  ticker_dict[word].bodies.append(body)
         except Exception as e:
            send_log_to_discord(f"Error al obtener precio de {word}: {e}")
   
   word_list = re.sub("[^\w]", " ",  body).split()
   for count, word in enumerate(word_list):
      if word.isupper() and len(word) != 1 and (word.upper() not in blacklist_words) and len(word) <= 5 and word.isalpha():
         try:
            if word != "ROPE":
               price = IEXStock(word).get_price()
         except Exception as e:
            continue
      
         if word in ticker_dict:
            ticker_dict[word].count += 1
            ticker_dict[word].bodies.append(body)
         else:
            ticker_dict[word] = Ticker(word)
            ticker_dict[word].count = 1
            ticker_dict[word].bodies.append(body)

   return ticker_dict

def get_url(key, value, total_count):
   mention = ("mentions", "mention") [value == 1]
   if int(value / total_count * 100) == 0:
         perc_mentions = "<1"
   else:
         perc_mentions = int(value / total_count * 100)
   if key == "ROPE":
      return "${0} | [{1} {2} ({3}% of all mentions)](https://www.homedepot.com/b/Hardware-Chains-Ropes-Rope/N-5yc1vZc2gr)".format(key, value, mention, perc_mentions)
   else:
      return "${0} | [{1} {2} ({3}% of all mentions)](https://finance.yahoo.com/quote/{0}?p={0})".format(key, value, mention, perc_mentions)

def final_post(subreddit, text):
   title = str(get_date()) + " | Today's Top 25 WSB Tickers"
   send_log_to_discord(f"Publicando en Reddit: {title}")
   print("\nPosting...")
   print(title)
   subreddit.submit(title, selftext=text)

def get_date():
   now = datetime.datetime.now()
   return now.strftime("%b %d, %Y")

def setup(sub):
   if sub == "":
      sub = "wallstreetbets"

   with open("config.json") as json_data_file:
      data = json.load(json_data_file)

   reddit = praw.Reddit(client_id=data["login"]["client_id"], client_secret=data["login"]["client_secret"],
                        username=data["login"]["username"], password=data["login"]["password"],
                        user_agent=data["login"]["user_agent"])
   subreddit = reddit.subreddit(sub)
   return subreddit

def run(mode, sub, num_submissions):
   send_log_to_discord(f"Bot iniciado: sub={sub}, num_submissions={num_submissions}, modo={'test' if mode else 'bot'}")
   ticker_dict = {}
   text = ""
   total_count = 0
   within24_hrs = False

   subreddit = setup(sub)
   new_posts = subreddit.new(limit=num_submissions)

   for count, post in enumerate(new_posts):
      if not post.clicked:
         ticker_dict = parse_section(ticker_dict, post.title)

         if "Daily Discussion Thread - " in post.title:
            if not within24_hrs:
               within24_hrs = True
            else:
               msg = f"Total posts searched: {count} | Total ticker mentions: {total_count}"
               print(f"\n{msg}")
               send_log_to_discord(msg)
               break
         
         comments = post.comments
         for comment in comments:
            if isinstance(comment, MoreComments):
               continue
            ticker_dict = parse_section(ticker_dict, comment.body)

            replies = comment.replies
            for rep in replies:
               if isinstance(rep, MoreComments):
                  continue
               ticker_dict = parse_section(ticker_dict, rep.body)
         
         progress_msg = f"Progress: {count + 1} / {num_submissions} posts"
         sys.stdout.write("\r" + progress_msg)
         sys.stdout.flush()
         if count % 50 == 0:
            send_log_to_discord(progress_msg)

   text = "To help you YOLO your money away, here are all of the tickers mentioned at least 10 times in all the posts within the past 24 hours (and links to their Yahoo Finance page) along with a sentiment analysis percentage:"
   text += "\n\nTicker | Mentions | Bullish (%) | Neutral (%) | Bearish (%)\n:- | :- | :- | :- | :-"

   total_mentions = 0
   ticker_list = []
   for key in ticker_dict:
      total_mentions += ticker_dict[key].count
      ticker_list.append(ticker_dict[key])

   ticker_list = sorted(ticker_list, key=operator.attrgetter("count"), reverse=True)

   for ticker in ticker_list:
      Ticker.analyze_sentiment(ticker)

   for count, ticker in enumerate(ticker_list):
      if count == 25:
         break
      
      url = get_url(ticker.ticker, ticker.count, total_mentions)
      text += "\n{} | {} | {} | {}".format(url, ticker.bullish, ticker.bearish, ticker.neutral)

   text += "\n\nTake a look at my [source code](https://github.com/RyanElliott10/wsbtickerbot) and make some contributions if you're interested."

   if not mode:
      final_post(subreddit, text)
      send_log_to_discord("Posteo finalizado en Reddit.")
   else:
      send_log_to_discord("Modo test: No se publica en Reddit.")
      print("\nNot posting to reddit because you're in test mode\n\n*************************************************\n")
      print(text)
      send_log_to_discord("Texto generado:\n" + text[:1900])  # Discord limita a 2000 caracteres por mensaje

class Ticker:
   def __init__(self, ticker):
      self.ticker = ticker
      self.count = 0
      self.bodies = []
      self.pos_count = 0
      self.neg_count = 0
      self.bullish = 0
      self.bearish = 0
      self.neutral = 0
      self.sentiment = 0 # 0 is neutral

   def analyze_sentiment(self):
      analyzer = SentimentIntensityAnalyzer()
      neutral_count = 0
      for text in self.bodies:
         sentiment = analyzer.polarity_scores(text)
         if (sentiment["compound"] > .005) or (sentiment["pos"] > abs(sentiment["neg"])):
            self.pos_count += 1
         elif (sentiment["compound"] < -.005) or (abs(sentiment["neg"]) > sentiment["pos"]):
            self.neg_count += 1
         else:
            neutral_count += 1

      self.bullish = int(self.pos_count / len(self.bodies) * 100)
      self.bearish = int(self.neg_count / len(self.bodies) * 100)
      self.neutral = int(neutral_count / len(self.bodies) * 100)

if __name__ == "__main__":
   mode = 0
   num_submissions = 500
   sub = "wallstreetbets"

   if len(sys.argv) > 2:
      mode = 1
      num_submissions = int(sys.argv[2])

   send_log_to_discord("wsbtickerbot.py iniciado")
   run(mode, sub, num_submissions)
   send_log_to_discord("wsbtickerbot.py terminó su ejecución")
