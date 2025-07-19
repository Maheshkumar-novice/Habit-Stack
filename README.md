# HabitStack

Personal life organizer with habit tracking, daily notes, todo list management, reading list, birthday reminders, watchlist, sports news aggregation, and comprehensive data management.

## Quick Start

```bash
# Install dependencies
uv sync

# Initialize database (creates encryption tables)
uv run python -c "from database import init_db; init_db()"

# Run the application
uv run python app.py

# Visit http://localhost:8000/habitstack/
```

## Features

- Habit tracking with streaks and points
- Daily notes and journaling
- Todo list management with smart organization
- Reading list with progress tracking and ratings
- Birthday reminders with relationship tracking
- Movies/series watchlist with progress tracking
- Sports news aggregation from multiple sources (BBC Sport, Sky Sports, Goal.com, Reddit r/soccer)
- Modular data export/import with file analysis
- Comprehensive account management with password updates
- Progressive Web App (PWA) for mobile installation
- Fully mobile-responsive design optimized for all devices

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
├── models/             # Data models (user, habit, note, todo, reading, birthday, watchlist, sports, data_manager)
├── auth.py             # Authentication routes
├── habits.py           # Habit management
├── notes.py            # Daily notes
├── todos.py            # Todo list management
├── reading.py          # Reading list management
├── birthdays.py        # Birthday reminders
├── watchlist.py        # Movies/series tracking
├── sports.py           # Sports news aggregation
├── settings.py         # Account and data management
└── templates/          # HTML templates with mobile optimization
```

## Routes

All routes prefixed with `/habitstack/`:

- `/` - Dashboard with habit tracking
- `/login` `/signup` `/logout` - Authentication
- `/habits` - Habit management with streaks
- `/notes` - Daily journaling with date navigation
- `/todos` - Todo list with smart organization
- `/reading` - Reading list with progress tracking and ratings
- `/birthdays` - Birthday reminders with relationship tracking
- `/watchlist` - Movies/series tracking with progress
- `/sports` - Football transfer news aggregation with multi-source display
- `/settings` - Account and modular data management