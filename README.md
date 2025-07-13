# HabitStack

Personal life organizer with habit tracking, daily notes, birthday reminders, watchlist, and data management.

## Quick Start

```bash
# Install dependencies
uv sync

# Run the application
uv run python app.py

# Visit http://localhost:8000/habitstack/
```

## Features

- Habit tracking with streaks and points
- Daily notes and journaling
- Birthday reminders
- Movies/series watchlist
- Data export/import
- Account management
- Progressive Web App (PWA)
- Mobile-responsive design

## Technology

- Flask backend with modular blueprints
- SQLite database with connection pooling
- Tailwind CSS for responsive design
- Session-based authentication
- Form-based interactions (no JavaScript frameworks)

## Development

```bash
uv run python app.py    # Run server
uv sync                 # Install dependencies
uv add <package>        # Add new dependency
```

## Architecture

```
├── app.py              # Main Flask application
├── database.py         # Database connection and tables
├── models/             # Data models (user, habit, note, birthday, watchlist)
├── auth.py             # Authentication routes
├── habits.py           # Habit management
├── notes.py            # Daily notes
├── birthdays.py        # Birthday reminders
├── watchlist.py        # Movies/series tracking
├── settings.py         # Account and data management
└── templates/          # HTML templates
```

## Routes

All routes prefixed with `/habitstack/`:

- `/` - Dashboard
- `/login` `/signup` `/logout` - Authentication
- `/habits` - Habit management
- `/notes` - Daily journaling
- `/birthdays` - Birthday reminders
- `/watchlist` - Movies/series tracking
- `/settings` - Account and data management