"""
Reading list model for book tracking and management
"""

from datetime import datetime
from typing import Optional, List, Dict
from database import get_db


class Reading:
    """Reading list model for book tracking and management"""
    
    @staticmethod
    def create(user_id: int, title: str, author: str, total_pages: int = None, 
               status: str = 'want_to_read', rating: int = None, notes: str = None) -> int:
        """Create a new book entry for user"""
        with get_db() as conn:
            cursor = conn.execute("""
                INSERT INTO reading_list (user_id, title, author, total_pages, status, rating, notes) 
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (user_id, title, author, total_pages, status, rating, notes))
            conn.commit()
            return cursor.lastrowid
    
    @staticmethod
    def get_user_books(user_id: int, status: str = None) -> List[Dict]:
        """Get reading list for a user, optionally filtered by status"""
        with get_db() as conn:
            if status:
                books = conn.execute("""
                    SELECT * FROM reading_list 
                    WHERE user_id = ? AND status = ? AND deleted_at IS NULL
                    ORDER BY date_added DESC
                """, (user_id, status)).fetchall()
            else:
                books = conn.execute("""
                    SELECT * FROM reading_list 
                    WHERE user_id = ? AND deleted_at IS NULL
                    ORDER BY 
                        CASE status 
                            WHEN 'currently_reading' THEN 1 
                            WHEN 'want_to_read' THEN 2 
                            WHEN 'completed' THEN 3 
                        END,
                        date_added DESC
                """, (user_id,)).fetchall()
            
            return [dict(book) for book in books]
    
    @staticmethod
    def get_books_by_status(user_id: int) -> Dict[str, List[Dict]]:
        """Get reading list organized by status"""
        with get_db() as conn:
            books = conn.execute("""
                SELECT * FROM reading_list 
                WHERE user_id = ? AND deleted_at IS NULL
                ORDER BY date_added DESC
            """, (user_id,)).fetchall()
            
            result = {
                'currently_reading': [],
                'want_to_read': [],
                'completed': []
            }
            
            for book in books:
                book_dict = dict(book)
                # Calculate reading progress percentage
                if book_dict['total_pages'] and book_dict['current_page']:
                    book_dict['progress_percentage'] = min(100, int((book_dict['current_page'] / book_dict['total_pages']) * 100))
                else:
                    book_dict['progress_percentage'] = 0
                
                status = book_dict['status']
                if status in result:
                    result[status].append(book_dict)
            
            return result
    
    @staticmethod
    def get_by_id(book_id: int, user_id: int) -> Optional[Dict]:
        """Get specific book by ID for user"""
        with get_db() as conn:
            book = conn.execute("""
                SELECT * FROM reading_list 
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """, (book_id, user_id)).fetchone()
            return dict(book) if book else None
    
    @staticmethod
    def update(book_id: int, user_id: int, title: str, author: str, 
               total_pages: int = None, current_page: int = None, status: str = None,
               rating: int = None, notes: str = None) -> bool:
        """Update book details"""
        with get_db() as conn:
            cursor = conn.execute("""
                UPDATE reading_list 
                SET title = ?, author = ?, total_pages = ?, current_page = ?, 
                    status = ?, rating = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """, (title, author, total_pages, current_page, status, rating, notes, book_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def update_status(book_id: int, user_id: int, status: str) -> bool:
        """Update book reading status"""
        with get_db() as conn:
            # If marking as completed, set completion date
            if status == 'completed':
                cursor = conn.execute("""
                    UPDATE reading_list 
                    SET status = ?, date_completed = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ? AND deleted_at IS NULL
                """, (status, book_id, user_id))
            else:
                cursor = conn.execute("""
                    UPDATE reading_list 
                    SET status = ?, date_completed = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ? AND deleted_at IS NULL
                """, (status, book_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def update_progress(book_id: int, user_id: int, current_page: int) -> bool:
        """Update current page reading progress"""
        with get_db() as conn:
            cursor = conn.execute("""
                UPDATE reading_list 
                SET current_page = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """, (current_page, book_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def mark_completed(book_id: int, user_id: int, rating: int = None) -> bool:
        """Mark book as completed with optional rating"""
        with get_db() as conn:
            # Get total pages to set current_page to total
            book = conn.execute("""
                SELECT total_pages FROM reading_list 
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """, (book_id, user_id)).fetchone()
            
            if book:
                current_page = book['total_pages'] if book['total_pages'] else None
                cursor = conn.execute("""
                    UPDATE reading_list 
                    SET status = 'completed', current_page = ?, rating = ?, 
                        date_completed = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ? AND user_id = ? AND deleted_at IS NULL
                """, (current_page, rating, book_id, user_id))
                conn.commit()
                return cursor.rowcount > 0
            return False
    
    @staticmethod
    def delete(book_id: int, user_id: int) -> bool:
        """Soft delete book"""
        with get_db() as conn:
            cursor = conn.execute("""
                UPDATE reading_list 
                SET deleted_at = CURRENT_TIMESTAMP
                WHERE id = ? AND user_id = ? AND deleted_at IS NULL
            """, (book_id, user_id))
            conn.commit()
            return cursor.rowcount > 0
    
    @staticmethod
    def get_stats(user_id: int) -> Dict:
        """Get reading statistics for user"""
        with get_db() as conn:
            stats = conn.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'currently_reading' THEN 1 ELSE 0 END) as currently_reading,
                    SUM(CASE WHEN status = 'want_to_read' THEN 1 ELSE 0 END) as want_to_read,
                    SUM(CASE WHEN status = 'completed' AND strftime('%Y', date_completed) = strftime('%Y', 'now') THEN 1 ELSE 0 END) as completed_this_year
                FROM reading_list 
                WHERE user_id = ? AND deleted_at IS NULL
            """, (user_id,)).fetchone()
            
            result = dict(stats) if stats else {
                'total': 0, 'completed': 0, 'currently_reading': 0, 'want_to_read': 0, 'completed_this_year': 0
            }
            
            # Ensure all values are integers, not None
            return {
                'total': result.get('total', 0) or 0,
                'completed': result.get('completed', 0) or 0,
                'currently_reading': result.get('currently_reading', 0) or 0,
                'want_to_read': result.get('want_to_read', 0) or 0,
                'completed_this_year': result.get('completed_this_year', 0) or 0
            }
    
    @staticmethod
    def get_reading_progress_summary(user_id: int) -> Dict:
        """Get summary of reading progress for currently reading books"""
        with get_db() as conn:
            progress = conn.execute("""
                SELECT 
                    COUNT(*) as books_in_progress,
                    AVG(CASE WHEN total_pages > 0 THEN (current_page * 100.0 / total_pages) ELSE 0 END) as avg_progress_percentage,
                    SUM(current_page) as total_pages_read
                FROM reading_list 
                WHERE user_id = ? AND status = 'currently_reading' AND deleted_at IS NULL
            """, (user_id,)).fetchone()
            
            result = dict(progress) if progress else {
                'books_in_progress': 0, 'avg_progress_percentage': 0, 'total_pages_read': 0
            }
            
            return {
                'books_in_progress': result.get('books_in_progress', 0) or 0,
                'avg_progress_percentage': round(result.get('avg_progress_percentage', 0) or 0, 1),
                'total_pages_read': result.get('total_pages_read', 0) or 0
            }