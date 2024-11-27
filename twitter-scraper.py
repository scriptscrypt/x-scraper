import requests
from bs4 import BeautifulSoup
import json
import time
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import textwrap
import random
import os
from dataclasses import dataclass
from typing import List, Dict
import re

@dataclass
class AccountConfig:
    username: str
    keywords: Dict[str, List[str]] = None
    weight: float = 1.0

class TwitterMonitor:
    def __init__(self):
        """Initialize the Twitter monitor with Nitter instances"""
        self.nitter_instances = [
            "https://nitter.net",
            "https://nitter.cz",
            "https://nitter.it",
            "https://nitter.pw"
        ]
        
        # Enhanced keyword categories
        ai_keywords = ["ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt", "agents", "autonomous"]
        crypto_keywords = ["crypto", "blockchain", "web3", "defi", "nft"]
        solana_keywords = ["solana", "sol", "saga", "firedancer", "bonk"]
        ai_crypto_keywords = ["ai crypto", "ai trading", "ai blockchain", "ai agents", "autonomous agents"]
        
        # Initialize monitored accounts
        self.accounts = [
            AccountConfig(
                username="IrffanAsiff",
                keywords={
                    "AI": ai_keywords,
                    "Crypto": crypto_keywords,
                    "Solana": solana_keywords,
                    "AI x Crypto": ai_crypto_keywords
                },
                weight=1.2
            ),
            AccountConfig(
                username="yashhsm",
                keywords={
                    "AI": ai_keywords,
                    "Crypto": crypto_keywords,
                    "Solana": solana_keywords,
                    "AI x Crypto": ai_crypto_keywords
                },
                weight=1.1
            ),
            AccountConfig(
                username="0xMert_",
                keywords={
                    "AI": ai_keywords,
                    "Crypto": crypto_keywords,
                    "Solana": solana_keywords,
                    "AI x Crypto": ai_crypto_keywords
                },
                weight=1.2
            )
        ]
        
        self.tweets_cache = {}
        self.summary_data = {
            "trending_topics": [],
            "category_insights": {},
            "sentiment": "neutral"
        }

        self.name_components = {
            'ai_prefix': ["Neural", "Quantum", "Cyber", "Meta", "Synth", "Auto"],
            'sol_prefix': ["Sol", "Saga", "Nova", "Luna", "Star"],
            'suffix': ["AI", "Labs", "Protocol", "Network", "Agents", "Chain"]
        }

    def get_working_instance(self):
        """Try Nitter instances until finding a working one"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        for instance in self.nitter_instances:
            try:
                response = requests.get(f"{instance}/", headers=headers, timeout=10)
                if response.status_code == 200:
                    print(f"Using Nitter instance: {instance}")
                    return instance
            except:
                continue
        raise Exception("No working Nitter instance found")

    def parse_tweet_stats(self, stats_text: str) -> dict:
        """Parse tweet engagement statistics from text"""
        stats = {
            'retweet_count': 0,
            'reply_count': 0,
            'like_count': 0
        }
        
        try:
            # Extract numbers using regex, handling both digits and K/M suffixes
            numbers = re.findall(r'(\d+\.?\d*[KMk]?)', stats_text)
            
            if len(numbers) >= 3:
                for i, num in enumerate(numbers[:3]):
                    # Convert K/M suffixes to actual numbers
                    multiplier = 1
                    if num.lower().endswith('k'):
                        multiplier = 1000
                        num = num[:-1]
                    elif num.lower().endswith('m'):
                        multiplier = 1000000
                        num = num[:-1]
                    
                    value = float(num) * multiplier
                    
                    if i == 0:
                        stats['retweet_count'] = int(value)
                    elif i == 1:
                        stats['reply_count'] = int(value)
                    elif i == 2:
                        stats['like_count'] = int(value)
        
        except Exception as e:
            print(f"Error parsing stats text: {stats_text} - {str(e)}")
        
        return stats

    def fetch_tweets(self, hours: int = 24):
        """Fetch tweets from monitored accounts using Nitter"""
        nitter_instance = self.get_working_instance()
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for account in self.accounts:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(
                    f"{nitter_instance}/{account.username}",
                    headers=headers,
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"Error fetching tweets for {account.username}: {response.status_code}")
                    continue
                
                soup = BeautifulSoup(response.text, 'html.parser')
                tweets = []
                
                for tweet_div in soup.find_all('div', class_='timeline-item'):
                    try:
                        # Get tweet time
                        time_element = tweet_div.find('span', class_='tweet-date')
                        if not time_element or not time_element.find('a'):
                            continue
                        
                        tweet_time_str = time_element.find('a').get('title')
                        if not tweet_time_str:
                            continue
                        
                        try:
                            tweet_time = datetime.strptime(
                                tweet_time_str,
                                '%b %d, %Y · %I:%M %p UTC'
                            )
                        except ValueError:
                            continue
                        
                        if tweet_time < cutoff_time:
                            continue
                        
                        # Get tweet text
                        tweet_content = tweet_div.find('div', class_='tweet-content')
                        if not tweet_content:
                            continue
                        tweet_text = tweet_content.get_text(strip=True)
                        
                        # Get tweet stats
                        stats_div = tweet_div.find('div', class_='tweet-stats')
                        if not stats_div:
                            continue
                            
                        tweet_stats = self.parse_tweet_stats(stats_div.get_text())
                        
                        tweets.append({
                            'text': tweet_text,
                            'created_at': tweet_time,
                            'public_metrics': tweet_stats
                        })
                        
                    except Exception as e:
                        print(f"Error parsing tweet: {str(e)}")
                        continue
                
                self.tweets_cache[account.username] = tweets
                print(f"Fetched {len(tweets)} tweets from @{account.username}")
                
                # Add delay to avoid rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"Error fetching tweets for {account.username}: {str(e)}")
                continue

    def analyze_tweets(self):
        """Analyze tweets and generate insights"""
        category_topics = {}
        total_engagement = 0
        
        for username, tweets in self.tweets_cache.items():
            account = next(acc for acc in self.accounts if acc.username == username)
            
            for tweet in tweets:
                metrics = tweet['public_metrics']
                engagement = (
                    metrics['retweet_count'] + 
                    metrics['reply_count'] + 
                    metrics['like_count']
                ) * account.weight
                total_engagement += engagement
                
                # Analyze by category
                for category, keywords in account.keywords.items():
                    if category not in category_topics:
                        category_topics[category] = {}
                    
                    for keyword in keywords:
                        if keyword.lower() in tweet['text'].lower():
                            if keyword not in category_topics[category]:
                                category_topics[category][keyword] = 0
                            category_topics[category][keyword] += engagement

        # Process category insights
        for category, topics in category_topics.items():
            sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:3]
            self.summary_data["category_insights"][category] = sorted_topics

        # Overall trending topics
        all_topics = {}
        for category_data in category_topics.values():
            for topic, score in category_data.items():
                all_topics[topic] = all_topics.get(topic, 0) + score
                
        self.summary_data["trending_topics"] = sorted(
            all_topics.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

    def generate_project_name(self):
        """Generate a project name"""
        if random.choice([True, False]):
            prefix = random.choice(self.name_components['ai_prefix'])
        else:
            prefix = random.choice(self.name_components['sol_prefix'])
        
        suffix = random.choice(self.name_components['suffix'])
        name = f"{prefix}{suffix}"
        ticker = f"${name[:3].upper()}"
        return name, ticker

    def generate_image(self, output_path: str = "summary.png"):
        """Generate summary image"""
        width, height = 1200, 1000
        image = Image.new('RGB', (width, height), color='black')
        draw = ImageDraw.Draw(image)
        
        try:
            font = ImageFont.truetype("Arial.ttf", 40)
            small_font = ImageFont.truetype("Arial.ttf", 30)
            category_font = ImageFont.truetype("Arial.ttf", 35)
        except IOError:
            font = ImageFont.load_default()
            small_font = ImageFont.load_default()
            category_font = ImageFont.load_default()

        # Generate and draw project name
        name, ticker = self.generate_project_name()
        draw.text((50, 50), name, fill='white', font=font)
        draw.text((50, 100), ticker, fill='#14F195', font=font)

        # Draw overall trending topics
        y_offset = 180
        draw.text((50, y_offset), "Top Trending Topics:", fill='white', font=font)
        for topic, score in self.summary_data["trending_topics"]:
            y_offset += 45
            draw.text(
                (70, y_offset),
                f"• {topic}: {score:.0f}",
                fill='#14F195',
                font=small_font
            )

        # Draw category insights
        y_offset += 80
        for category, topics in self.summary_data["category_insights"].items():
            if topics:  # Only show categories with data
                draw.text((50, y_offset), f"{category}:", fill='#14F195', font=category_font)
                y_offset += 45
                for topic, score in topics:
                    draw.text(
                        (70, y_offset),
                        f"• {topic}: {score:.0f}",
                        fill='white',
                        font=small_font
                    )
                    y_offset += 40
                y_offset += 20

        # Save image
        image.save(output_path)
        return name, ticker

    def run_monitoring_cycle(self, duration_hours: int = 24):
        """Run a complete monitoring cycle"""
        print(f"Starting monitoring cycle for {duration_hours} hours...")
        
        try:
            self.fetch_tweets(duration_hours)
            print("Tweets fetched successfully")
            
            self.analyze_tweets()
            print("Tweet analysis completed")
            
            name, ticker = self.generate_image()
            print("Summary image generated")
            
            return {
                "name": name,
                "ticker": ticker,
                "trending_topics": self.summary_data["trending_topics"],
                "category_insights": self.summary_data["category_insights"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            print(f"Error in monitoring cycle: {str(e)}")
            raise

def main():
    monitor = TwitterMonitor()
    
    while True:
        try:
            results = monitor.run_monitoring_cycle()
            print(f"Generated summary for {results['name']} ({results['ticker']})")
            print("\nTrending topics:", results['trending_topics'])
            print("\nCategory insights:")
            for category, insights in results['category_insights'].items():
                print(f"\n{category}:")
                for topic, score in insights:
                    print(f"  • {topic}: {score:.0f}")
            
            time.sleep(72*60*60)  # 1 min
            
        except Exception as e:
            print(f"Error in monitoring cycle: {str(e)}")
            time.sleep(60)  # 1 min

if __name__ == "__main__":
    main()