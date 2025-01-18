import groq
import praw
import schedule

import sys
import time
import signal
import logging
from datetime import date, datetime
from logging.handlers import RotatingFileHandler

from typing import Optional, List, Tuple

import os
from dotenv import load_dotenv

import re
import json

import nltk
from nltk.corpus import stopwords
nltk.download('stopwords', quiet=True)

import argparse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        RotatingFileHandler(
            'bot.log',
            maxBytes=1024*1024,  # 1MB
            backupCount=5
        ),
        logging.StreamHandler()
    ]
)


class RedditGroqBot:
    def __init__(self):
        self.MAX_RETRIES = 5
        self.API_CALL_DELAY = 10
        self.MAX_DAILY_CALLS = 500
        self.TITLE_STORE = 'titles.json'
        self._load_environment()
        self._initialize_clients()
        self._initialize_tracking()
        self._setup_signal_handlers()
        
        logging.info('Bot initialized successfully')

    def _load_environment(self):
        """
        Load required environment variables and validate their presence.
        """
        load_dotenv()
        required_vars = [
            'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET',
            'REDDIT_USERNAME', 'REDDIT_PASSWORD',
            'SUBREDDIT', 'GROQ_API_KEY'
        ]
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise EnvironmentError(f"Missing required environment variables: {', '.join(missing)}")

    def _initialize_clients(self):
        """
        Initialize Reddit and Groq clients, using environment variables.
        """
        self.reddit = praw.Reddit(
            client_id=os.getenv('REDDIT_CLIENT_ID'),
            client_secret=os.getenv('REDDIT_CLIENT_SECRET'),
            username=os.getenv('REDDIT_USERNAME'),
            password=os.getenv('REDDIT_PASSWORD'),
            user_agent='GroqAIBot/1.0'
        )
        self.subreddit = self.reddit.subreddit(os.getenv('SUBREDDIT'))
        self.groq_client = groq.Groq(api_key=os.getenv('GROQ_API_KEY'))

    def _initialize_tracking(self):
        """
        Initialize tracking variables and load 2-grams from file.
        """
        self.api_calls_today = 0
        self.last_api_call = None
        self.current_date = date.today()
        self.generated_titles = set()
        self.used_2grams = set()
        self.stop_words = set(stopwords.words('english'))
        self._load_2grams()

    def _setup_signal_handlers(self):
        """
        Setup signal handlers for graceful shutdown.
        """
        signal.signal(signal.SIGINT, self._handle_shutdown)
        signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        """
        Handle shutdown signals by saving 2-grams and exiting.
        """
        logging.info("Shutdown signal received. Cleaning up...")
        self._save_2grams()
        sys.exit(0)

    def _load_2grams(self):
        """
        Load 2-grams from JSON, if available.
        """
        try:
            with open(self.TITLE_STORE, 'r') as f:
                data = json.load(f)
                self.used_2grams = set(data.get("2grams", []))
                logging.info(f"Loaded {len(self.used_2grams)} 2-grams")
        except FileNotFoundError:
            logging.warning(f"{self.TITLE_STORE} not found, starting fresh")
            self.used_2grams = set()
            self._save_2grams() # Create empty file
        except Exception as e:
            logging.error(f"Error loading {self.TITLE_STORE}: {str(e)}")

    def _save_2grams(self):
        """
        Save 2-grams to JSON file
        """
        try:
            with open(self.TITLE_STORE, 'w') as f:
                json.dump({"2grams": list(self.used_2grams)}, f)
                logging.info(f"Saved {len(self.used_2grams)} 2-grams")
        except Exception as e:
            logging.error(f"Error saving to {self.TITLE_STORE}: {str(e)}")

    def _check_rate_limits(self):
        """
        Check and enforce rate limits for API calls.
        """
        current_date = date.today()
        if current_date != self.current_date:
            self.api_calls_today = 0
            self.current_date = current_date
            logging.info(f"API calls reset for {self.current_date}")

        if self.api_calls_today >= self.MAX_DAILY_CALLS:
            raise Exception("Daily API limit reached")

        if self.last_api_call:
            time_since_last_call = time.time() - self.last_api_call
            if time_since_last_call < self.API_CALL_DELAY:
                time.sleep(self.API_CALL_DELAY - time_since_last_call)

        self.last_api_call = time.time()
        self.api_calls_today += 1

    def generate_content(self) -> tuple[Optional[str], Optional[str]]:
        for attempt in range(self.MAX_RETRIES):
            try:
                self._check_rate_limits()

                excluded_topics = ", ".join([f'"{two_gram}"' for two_gram in self.used_2grams])
                
                prompt = f"""Generate an engaging Reddit post for: {self.subreddit}
                Format:
                Title: [Generated title]
                Content: [Generated content]

                Major Requirements and Guidelines:
                - Unique, lesser-known insights
                - Engaging narrative style
                - Clear examples and explanations
                - Avoid these topics: {excluded_topics}
                """

                response = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.3-70b-versatile",
                    temperature=0.7,
                    max_tokens=800,
                    top_p=0.95
                )
                content = response.choices[0].message.content
                
                title, body = self._parse_content(content)
                if not title or not body:
                    logging.error("Failed to generate content. Retrying...")
                    continue

                used_titles = self._extract_2grams(title)
                if used_titles.isdisjoint(self.used_2grams):
                    self.used_2grams.update(used_titles)
                    self._save_2grams()
                    logging.info(f'Generated unique content: "{title}"')
                    return title, body

                logging.warning(f"Attempt {attempt + 1}: Duplicate content detected")

            except Exception as e:
                logging.error(f"Error generating content (attempt {attempt + 1}): {str(e)}")

            finally:
                time.sleep(5 * (attempt + 1))

        logging.error("Failed to generate unique content after max retries")
        return None, None

    def _parse_content(self, content: str) -> Tuple[str, str]:
        lines = content.split('\n')
        title = next((line.replace('Title:', '').strip() for line in lines 
                     if line.strip().startswith('Title:')), '')
        body = '\n'.join(line for line in lines[2:] 
                        if not line.strip().startswith('Title:'))
        body = body.replace('Content:', '').strip()
        
        return self._strip_enclosing_quotes(title), self._strip_enclosing_quotes(body)

    def _strip_enclosing_quotes(self, text: str) -> str:
        return text[1:-1] if text.startswith('"') and text.endswith('"') else text

    def _extract_2grams(self, title: str) -> set:
        words = re.sub(r'[^a-zA-Z\s]', '', title).lower().split()
        filtered_words = [word for word in words 
                         if word.isalpha() and word not in self.stop_words]
        return set(f"{filtered_words[i]} {filtered_words[i + 1]}"
                  for i in range(len(filtered_words) - 1))

    def create_post(self) -> Optional[str]:
        try:
            title, body = self.generate_content()
            post = self.subreddit.submit(title=title, selftext=body)
            logging.info(f"Successfully created post: {post.url}")
            return post.url
        except Exception as e:
            logging.error(f"Error creating post: {str(e)}")
            return None


def schedule_posts(times: List[str] = None):
    bot = RedditGroqBot()

    if not times: # Default: every hour
        times = [f"{hour:02d}:00" for hour in range(24)]

    for time_str in times:
        try:
            datetime.strptime(time_str, "%H:%M")  # Validate time format
            schedule.every().day.at(time_str).do(bot.create_post)
            logging.info(f"Scheduled post at {time_str}")
        except ValueError:
            logging.error(f"Invalid time format: {time_str}")

    logging.info('Bot started, running scheduled tasks...')
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            logging.error(f'Schedule error: {str(e)}')
        finally:
            time.sleep(60)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Schedule Reddit posts at specific times.")
    parser.add_argument(
        "-t", "--times",
        type=str,
        nargs="+",
        help="Times to schedule posts (HH:MM format). Default: every hour"
    )
    args = parser.parse_args()

    schedule_posts(args.times)