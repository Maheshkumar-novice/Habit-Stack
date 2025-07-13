"""
Models package for HabitStack application

This package provides all the data models:
- User: Authentication and user management
- Habit: Habit tracking and completion management
- DailyNote: Daily journaling functionality
- Birthday: Birthday reminder system
- Watchlist: Movies and series tracking
"""

from .user import User
from .habit import Habit
from .note import DailyNote
from .birthday import Birthday
from .watchlist import Watchlist

__all__ = ['User', 'Habit', 'DailyNote', 'Birthday', 'Watchlist']