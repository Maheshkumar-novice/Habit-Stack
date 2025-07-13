"""
Watchlist model for movies and series tracking
"""

from typing import Optional, List, Dict
from database import get_db


class Watchlist:
    """Watchlist model for movies and series tracking"""
    
    @staticmethod
    def get_user_watchlist(user_id: int, status: str = None) -> List[Dict]:
        """Get watchlist items for a user, optionally filtered by status"""
        with get_db() as conn:
            if status:
                items = conn.execute("""
                    SELECT * FROM watchlist 
                    WHERE user_id = ? AND status = ?
                    ORDER BY date_added DESC
                """, (user_id, status)).fetchall()
            else:
                items = conn.execute("""
                    SELECT * FROM watchlist 
                    WHERE user_id = ?
                    ORDER BY 
                        CASE status 
                            WHEN 'watching' THEN 1 
                            WHEN 'want_to_watch' THEN 2 
                            WHEN 'completed' THEN 3 
                        END,
                        date_added DESC
                """, (user_id,)).fetchall()
            
            return [dict(item) for item in items]
    
    @staticmethod
    def get_watchlist_by_status(user_id: int) -> Dict[str, List[Dict]]:
        """Get watchlist items organized by status"""
        with get_db() as conn:
            items = conn.execute("""
                SELECT * FROM watchlist 
                WHERE user_id = ?
                ORDER BY date_added DESC
            """, (user_id,)).fetchall()
            
            result = {
                'watching': [],
                'want_to_watch': [],
                'completed': []
            }
            
            for item in items:
                item_dict = dict(item)
                if item['status'] in result:
                    result[item['status']].append(item_dict)
            
            return result
    
    @staticmethod
    def get_watchlist_item(item_id: int, user_id: int) -> Optional[Dict]:
        """Get a specific watchlist item"""
        with get_db() as conn:
            item = conn.execute(
                "SELECT * FROM watchlist WHERE id = ? AND user_id = ?",
                (item_id, user_id)
            ).fetchone()
            return dict(item) if item else None
    
    @staticmethod
    def create_watchlist_item(user_id: int, title: str, item_type: str,
                            genre: str = None, priority: str = 'medium',
                            total_episodes: int = None, release_year: int = None,
                            notes: str = None) -> int:
        """Create a new watchlist item"""
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO watchlist (user_id, title, type, genre, priority, 
                                     total_episodes, release_year, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (user_id, title.strip(), item_type,
                  genre.strip() if genre else None,
                  priority,
                  total_episodes,
                  release_year,
                  notes.strip() if notes else None))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def update_watchlist_item(item_id: int, user_id: int, title: str, item_type: str,
                            genre: str = None, status: str = None, priority: str = None,
                            rating: int = None, current_episode: int = None,
                            total_episodes: int = None, release_year: int = None,
                            notes: str = None) -> bool:
        """Update an existing watchlist item"""
        with get_db() as conn:
            # Build dynamic update query
            updates = []
            params = []
            
            updates.extend(['title = ?', 'type = ?'])
            params.extend([title.strip(), item_type])
            
            if genre is not None:
                updates.append('genre = ?')
                params.append(genre.strip() if genre else None)
            
            if status is not None:
                updates.append('status = ?')
                params.append(status)
                
                # Set completion date if marking as completed
                if status == 'completed':
                    updates.append('date_completed = CURRENT_DATE')
                elif status in ['want_to_watch', 'watching']:
                    updates.append('date_completed = NULL')
            
            if priority is not None:
                updates.append('priority = ?')
                params.append(priority)
            
            if rating is not None:
                updates.append('rating = ?')
                params.append(rating)
            
            if current_episode is not None:
                updates.append('current_episode = ?')
                params.append(current_episode)
            
            if total_episodes is not None:
                updates.append('total_episodes = ?')
                params.append(total_episodes)
            
            if release_year is not None:
                updates.append('release_year = ?')
                params.append(release_year)
            
            if notes is not None:
                updates.append('notes = ?')
                params.append(notes.strip() if notes else None)
            
            params.extend([item_id, user_id])
            
            cursor = conn.execute(f"""
                UPDATE watchlist 
                SET {', '.join(updates)}
                WHERE id = ? AND user_id = ?
            """, params)
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def update_episode_progress(item_id: int, user_id: int, current_episode: int) -> bool:
        """Update episode progress for a series"""
        with get_db() as conn:
            cursor = conn.execute("""
                UPDATE watchlist 
                SET current_episode = ?, status = 'watching'
                WHERE id = ? AND user_id = ?
            """, (current_episode, item_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def mark_as_completed(item_id: int, user_id: int, rating: int = None) -> bool:
        """Mark an item as completed"""
        with get_db() as conn:
            if rating is not None:
                cursor = conn.execute("""
                    UPDATE watchlist 
                    SET status = 'completed', date_completed = CURRENT_DATE, rating = ?
                    WHERE id = ? AND user_id = ?
                """, (rating, item_id, user_id))
            else:
                cursor = conn.execute("""
                    UPDATE watchlist 
                    SET status = 'completed', date_completed = CURRENT_DATE
                    WHERE id = ? AND user_id = ?
                """, (item_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def delete_watchlist_item(item_id: int, user_id: int) -> bool:
        """Delete a watchlist item"""
        with get_db() as conn:
            cursor = conn.execute(
                "DELETE FROM watchlist WHERE id = ? AND user_id = ?",
                (item_id, user_id)
            )
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        """Get watchlist statistics"""
        with get_db() as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'watching' THEN 1 ELSE 0 END) as watching,
                    SUM(CASE WHEN status = 'want_to_watch' THEN 1 ELSE 0 END) as want_to_watch,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN type = 'movie' THEN 1 ELSE 0 END) as movies,
                    SUM(CASE WHEN type = 'series' THEN 1 ELSE 0 END) as series
                FROM watchlist 
                WHERE user_id = ?
            """, (user_id,)).fetchone()
            
            return dict(stats) if stats else {
                'total': 0, 'watching': 0, 'want_to_watch': 0, 
                'completed': 0, 'movies': 0, 'series': 0
            }