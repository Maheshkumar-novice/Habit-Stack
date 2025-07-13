"""
Database connection and initialization for HabitStack
"""

import sqlite3
import threading
import time
from contextlib import contextmanager
from queue import Queue, Empty

# Database setup
DB_PATH = "habitstack.db"

class SQLiteConnectionPool:
    """Simple connection pool for SQLite"""
    
    def __init__(self, database_path, max_connections=10, timeout=30):
        self.database_path = database_path
        self.max_connections = max_connections
        self.timeout = timeout
        self.pool = Queue(maxsize=max_connections)
        self.lock = threading.Lock()
        self._created_connections = 0
        
        # Pre-create some connections
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize the pool with a few connections"""
        for _ in range(min(3, self.max_connections)):
            conn = self._create_connection()
            if conn:
                self.pool.put(conn)
    
    def _create_connection(self):
        """Create a new database connection"""
        try:
            conn = sqlite3.connect(
                self.database_path,
                check_same_thread=False,  # Allow use across threads
                timeout=self.timeout
            )
            conn.row_factory = sqlite3.Row
            
            # Enable WAL mode for better concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            
            # Other performance optimizations
            conn.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL, still safe with WAL
            conn.execute("PRAGMA cache_size=10000")    # 10MB cache
            conn.execute("PRAGMA foreign_keys=ON")     # Enforce foreign key constraints
            
            with self.lock:
                self._created_connections += 1
            
            return conn
        except Exception as e:
            print(f"Error creating database connection: {e}")
            return None
    
    def get_connection(self):
        """Get a connection from the pool"""
        try:
            # Try to get an existing connection
            conn = self.pool.get_nowait()
            
            # Test if connection is still valid
            try:
                conn.execute("SELECT 1")
                return conn
            except:
                # Connection is bad, create a new one
                conn.close()
                return self._create_connection()
                
        except Empty:
            # No connections available, create new one if under limit
            with self.lock:
                if self._created_connections < self.max_connections:
                    return self._create_connection()
            
            # Wait for a connection to become available
            try:
                conn = self.pool.get(timeout=self.timeout)
                return conn
            except Empty:
                raise Exception("No database connections available")
    
    def return_connection(self, conn):
        """Return a connection to the pool"""
        if conn:
            try:
                # Reset any uncommitted transactions
                conn.rollback()
                self.pool.put_nowait(conn)
            except:
                # Pool is full or connection is bad, just close it
                conn.close()
                with self.lock:
                    self._created_connections -= 1
    
    def close_all(self):
        """Close all connections in the pool"""
        while not self.pool.empty():
            try:
                conn = self.pool.get_nowait()
                conn.close()
            except Empty:
                break
        
        with self.lock:
            self._created_connections = 0

# Global connection pool instance
_connection_pool = None

def get_connection_pool():
    """Get the global connection pool, creating it if necessary"""
    global _connection_pool
    if _connection_pool is None:
        _connection_pool = SQLiteConnectionPool(DB_PATH)
    return _connection_pool

@contextmanager
def get_db():
    """Get database connection from pool with proper cleanup"""
    pool = get_connection_pool()
    conn = pool.get_connection()
    try:
        yield conn
    finally:
        pool.return_connection(conn)

def init_db():
    """Initialize database tables with WAL mode"""
    with get_db() as conn:
        # Enable WAL mode (will be applied to all subsequent connections via pool)
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Create tables
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE TABLE IF NOT EXISTS habits (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                description TEXT,
                points INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
            
            CREATE TABLE IF NOT EXISTS habit_completions (
                id INTEGER PRIMARY KEY,
                habit_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                completion_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habits (id),
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(habit_id, completion_date)
            );
            
            CREATE TABLE IF NOT EXISTS daily_notes (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                note_date DATE NOT NULL,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                UNIQUE(user_id, note_date)
            );
            
            CREATE TABLE IF NOT EXISTS birthdays (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                birth_date DATE NOT NULL,
                relationship_type TEXT,
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """)
        
        # Create indexes for better performance
        conn.executescript("""
            CREATE INDEX IF NOT EXISTS idx_habits_user_id ON habits(user_id);
            CREATE INDEX IF NOT EXISTS idx_completions_habit_date ON habit_completions(habit_id, completion_date);
            CREATE INDEX IF NOT EXISTS idx_completions_user_date ON habit_completions(user_id, completion_date);
            CREATE INDEX IF NOT EXISTS idx_notes_user_date ON daily_notes(user_id, note_date);
            CREATE INDEX IF NOT EXISTS idx_birthdays_user_id ON birthdays(user_id);
            CREATE INDEX IF NOT EXISTS idx_birthdays_birth_date ON birthdays(birth_date);
        """)
        
        conn.commit()

def close_db_pool():
    """Close the connection pool (useful for testing or shutdown)"""
    global _connection_pool
    if _connection_pool:
        _connection_pool.close_all()
        _connection_pool = None