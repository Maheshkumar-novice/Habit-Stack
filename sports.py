"""
Sports news routes for HabitStack
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from datetime import datetime
import time
import re
import json
import requests
import feedparser
from bs4 import BeautifulSoup
from models.sports import SportsNews
from utils import require_auth, get_current_user

sports_bp = Blueprint('sports', __name__, url_prefix='/habitstack')

class TransferNewsFetcher:
    """Fetches transfer news from multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def fetch_bbc_sport_transfers(self):
        """Fetch transfer news from BBC Sport RSS feed"""
        try:
            feed_url = "http://feeds.bbci.co.uk/sport/football/rss.xml"
            feed = feedparser.parse(feed_url)
            
            transfers = []
            for entry in feed.entries[:10]:  # Get latest 10 entries
                if any(keyword in entry.title.lower() for keyword in ['transfer', 'sign', 'move', 'deal', 'join']):
                    transfers.append({
                        'title': entry.title,
                        'link': entry.link,
                        'published': entry.get('published', 'No date'),
                        'summary': entry.get('summary', 'No summary'),
                        'source': 'BBC Sport'
                    })
            return transfers
        except Exception as e:
            print(f"Error fetching BBC Sport: {e}")
            return []
    
    def fetch_reddit_soccer_transfers(self):
        """Fetch transfer discussions from Reddit Soccer (JSON API)"""
        try:
            url = "https://www.reddit.com/r/soccer/search.json"
            params = {
                'q': 'transfer OR signing OR deal',
                'sort': 'new',
                'limit': 10,
                'restrict_sr': 1,
                't': 'day'
            }
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            transfers = []
            for post in data['data']['children']:
                post_data = post['data']
                if any(keyword in post_data['title'].lower() for keyword in ['transfer', 'sign', 'deal', 'move', 'join']):
                    transfers.append({
                        'title': post_data['title'],
                        'link': f"https://reddit.com{post_data['permalink']}",
                        'published': datetime.fromtimestamp(post_data['created_utc']).strftime('%Y-%m-%d %H:%M'),
                        'summary': post_data.get('selftext', '')[:200] + '...' if post_data.get('selftext') else post_data['title'],
                        'source': 'Reddit r/soccer'
                    })
            
            return transfers
        except Exception as e:
            print(f"Error fetching Reddit: {e}")
            return []

class HabitStackTransferNewsFetcher(TransferNewsFetcher):
    """Fetches transfer news from multiple sources (reusing original news.py implementation)"""
    
    def fetch_sky_sports_transfers(self):
        """Fetch transfer news from Sky Sports (updated selectors)"""
        try:
            url = "https://www.skysports.com/football/transfer-news"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            transfers = []
            # Look for h3 elements with sdc-site-tile__headline class
            headlines = soup.find_all('h3', class_='sdc-site-tile__headline')
            
            for headline in headlines[:6]:  # Limit to 6 for web display
                title = headline.get_text(strip=True)
                if title and len(title) > 15:
                    # Check if it's transfer related
                    if any(word in title.lower() for word in ['transfer', 'sign', 'move', 'deal', 'join', 'bid']):
                        # Look for link
                        link_elem = headline.find('a') or headline.find_parent('a')
                        link = ''
                        if link_elem:
                            link = link_elem.get('href', '')
                            if link and not link.startswith('http'):
                                link = 'https://www.skysports.com' + link
                        
                        transfers.append({
                            'title': title,
                            'link': link,
                            'published': 'Recent',
                            'summary': title[:150] + '...' if len(title) > 150 else title,
                            'source': 'Sky Sports'
                        })
            
            return transfers
        except Exception as e:
            print(f"Error fetching Sky Sports: {e}")
            return []

    def fetch_goal_transfers(self):
        """Fetch transfer news from Goal.com (updated URL)"""
        try:
            url = "https://www.goal.com/en/transfers"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            transfers = []
            # Look for headlines
            headlines = soup.find_all(['h1', 'h2', 'h3', 'h4'])
            
            for headline in headlines[:8]:  # Limit to 8 for web display
                title = headline.get_text(strip=True)
                if title and len(title) > 15:
                    # Check if it's transfer related
                    if any(word in title.lower() for word in ['transfer', 'sign', 'move', 'deal', 'join']):
                        # Look for link
                        link_elem = headline.find('a') or headline.find_parent('a')
                        link = ''
                        if link_elem:
                            link = link_elem.get('href', '')
                            if link and not link.startswith('http'):
                                link = 'https://www.goal.com' + link
                        
                        transfers.append({
                            'title': title,
                            'link': link,
                            'published': 'Recent',
                            'summary': title[:150] + '...' if len(title) > 150 else title,
                            'source': 'Goal.com'
                        })
            
            return transfers
        except Exception as e:
            print(f"Error fetching Goal.com: {e}")
            return []

    def fetch_transfermarkt_news(self):
        """Fetch news from Transfermarkt (updated URL)"""
        try:
            url = "https://www.transfermarkt.com/statistik/neuestetransfers"
            response = self.session.get(url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            transfers = []
            # Look for transfer items in the table or list
            rows = soup.find_all('tr')
            
            for row in rows[:8]:  # Limit to 8 for web display
                # Look for player names and club information
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:
                    # Try to extract player and club info
                    player_cell = None
                    club_cells = []
                    
                    for cell in cells:
                        text = cell.get_text(strip=True)
                        if text and len(text) > 2:
                            if any(word in text.lower() for word in ['fc', 'united', 'city', 'real', 'barcelona']):
                                club_cells.append(text)
                            elif text and not any(char in text for char in ['€', '$', 'mil', 'k']):
                                if not player_cell:
                                    player_cell = text
                    
                    if player_cell and club_cells:
                        title = f"{player_cell} - {' to '.join(club_cells[:2])}"
                        transfers.append({
                            'title': title,
                            'link': 'https://www.transfermarkt.com/statistik/neuestetransfers',
                            'published': 'Recent',
                            'summary': title,
                            'source': 'Transfermarkt'
                        })
            
            return transfers
        except Exception as e:
            print(f"Error fetching Transfermarkt: {e}")
            return []
    
    def fetch_all_sources(self):
        """Fetch from all sources with error handling - adapted for HabitStack"""
        all_transfers = []
        
        # Use the original sources from news.py
        sources = [
            ("BBC Sport", self.fetch_bbc_sport_transfers),
            ("Sky Sports", self.fetch_sky_sports_transfers),
            ("Goal.com", self.fetch_goal_transfers),
            # ("Transfermarkt", self.fetch_transfermarkt_news),  # Disabled due to complex structure
            ("Reddit r/soccer", self.fetch_reddit_soccer_transfers),
        ]
        
        for source_name, fetch_func in sources:
            try:
                transfers = fetch_func()
                all_transfers.extend(transfers)
                time.sleep(0.5)  # Be respectful to servers
            except Exception as e:
                print(f"Failed to fetch from {source_name}: {e}")
                continue
        
        return all_transfers

@sports_bp.route('/sports')
@require_auth
def sports_news():
    """Display sports news page"""
    # Get current user
    user = get_current_user()
    
    # Initialize table if it doesn't exist
    SportsNews.create_table()
    
    # Get cached articles
    articles_by_source = SportsNews.get_articles_by_source()
    last_update = SportsNews.get_last_update()
    article_count = SportsNews.get_article_count()
    
    # If no cached articles or very few, show a message
    if article_count < 5:
        flash('No recent sports news cached. Click "Refresh News" to fetch latest articles.', 'info')
    
    return render_template('sports.html', 
                         user=user,
                         articles_by_source=articles_by_source,
                         last_update=last_update,
                         article_count=article_count)

@sports_bp.route('/sports/refresh', methods=['POST'])
@require_auth
def refresh_news():
    """Refresh sports news from all sources"""
    try:
        # Initialize table if it doesn't exist
        SportsNews.create_table()
        
        # Fetch new articles
        fetcher = HabitStackTransferNewsFetcher()
        new_articles = fetcher.fetch_all_sources()
        
        if new_articles:
            # Save to database
            saved_count = SportsNews.save_articles(new_articles)
            
            # Clean up old articles (keep last 7 days)
            cleaned_count = SportsNews.cleanup_old_articles(days=7)
            
            if saved_count > 0:
                flash(f'Successfully refreshed! Added {saved_count} new articles.', 'success')
            else:
                flash('Refresh completed. No new articles found.', 'info')
        else:
            flash('Unable to fetch news at this time. Please try again later.', 'warning')
            
    except Exception as e:
        flash(f'Error refreshing news: {str(e)}', 'error')
    
    return redirect(url_for('sports.sports_news'))

@sports_bp.route('/sports/clear', methods=['POST'])
@require_auth
def clear_news():
    """Clear all cached sports news"""
    try:
        cleared_count = SportsNews.clear_all_articles()
        flash(f'Cleared {cleared_count} cached articles.', 'success')
    except Exception as e:
        flash(f'Error clearing news: {str(e)}', 'error')
    
    return redirect(url_for('sports.sports_news'))