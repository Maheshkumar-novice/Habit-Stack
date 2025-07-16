"""
Sports news model for HabitStack.
Handles caching and management of sports news articles.
"""

from datetime import datetime, timedelta
import sqlite3
from typing import List, Dict, Optional
from database import get_db

class SportsNews:
    """Model for managing sports news articles with caching."""
    
    @staticmethod
    def create_table():
        """Create the sports_news table if it doesn't exist."""
        with get_db() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS sports_news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    link TEXT,
                    source TEXT NOT NULL,
                    published TEXT,
                    summary TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(title, source)
                )
            ''')
            # Create index for faster queries
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sports_news_created_at ON sports_news(created_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_sports_news_source ON sports_news(source)')
    
    @staticmethod
    def save_articles(articles: List[Dict]) -> int:
        """Save articles to database, avoiding duplicates."""
        if not articles:
            return 0
        
        saved_count = 0
        with get_db() as conn:
            for article in articles:
                try:
                    cursor = conn.execute('''
                        INSERT OR IGNORE INTO sports_news 
                        (title, link, source, published, summary)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (
                        article['title'],
                        article['link'],
                        article['source'],
                        article['published'],
                        article['summary']
                    ))
                    if cursor.rowcount > 0:
                        saved_count += 1
                except sqlite3.Error as e:
                    continue
            conn.commit()
        return saved_count
    
    @staticmethod
    def get_recent_articles(hours: int = 72) -> List[Dict]:
        """Get articles from the last N hours (default: 72 hours = 3 days)."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        # Format cutoff time to match database format (space instead of T)
        cutoff_str = cutoff_time.strftime('%Y-%m-%d %H:%M:%S')
        
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT title, link, source, published, summary, created_at
                FROM sports_news
                WHERE created_at > ?
                ORDER BY created_at DESC
            ''', (cutoff_str,))
            
            articles = []
            for row in cursor.fetchall():
                articles.append({
                    'title': row[0],
                    'link': row[1],
                    'source': row[2],
                    'published': row[3],
                    'summary': row[4],
                    'created_at': row[5]
                })
            
            return articles
    
    @staticmethod
    def get_articles_by_source() -> Dict[str, List[Dict]]:
        """Get recent articles grouped by source."""
        articles = SportsNews.get_recent_articles()
        
        # Group by source
        by_source = {}
        for article in articles:
            source = article['source']
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(article)
        
        return by_source
    
    @staticmethod
    def cleanup_old_articles(days: int = 7):
        """Remove articles older than N days."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        with get_db() as conn:
            cursor = conn.execute('''
                DELETE FROM sports_news
                WHERE created_at < ?
            ''', (cutoff_time.isoformat(),))
            return cursor.rowcount
    
    @staticmethod
    def get_article_count() -> int:
        """Get total number of cached articles."""
        with get_db() as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM sports_news')
            return cursor.fetchone()[0]
    
    @staticmethod
    def get_last_update() -> Optional[str]:
        """Get timestamp of most recent article."""
        with get_db() as conn:
            cursor = conn.execute('''
                SELECT MAX(created_at) FROM sports_news
            ''')
            result = cursor.fetchone()[0]
            if result:
                try:
                    dt = datetime.fromisoformat(result)
                    return dt.strftime('%Y-%m-%d %H:%M')
                except:
                    return result
            return None
    
    @staticmethod
    def clear_all_articles():
        """Clear all cached articles."""
        with get_db() as conn:
            cursor = conn.execute('DELETE FROM sports_news')
            conn.commit()
            return cursor.rowcount