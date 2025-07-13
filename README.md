# HabitStack

Personal life organizer with habit tracking, daily notes, todo list management, birthday reminders, watchlist, and comprehensive data management.

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
- Todo list management with smart organization
- Birthday reminders with relationship tracking
- Movies/series watchlist with progress tracking
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
├── models/             # Data models (user, habit, note, todo, birthday, watchlist, data_manager)
├── auth.py             # Authentication routes
├── habits.py           # Habit management
├── notes.py            # Daily notes
├── todos.py            # Todo list management
├── birthdays.py        # Birthday reminders
├── watchlist.py        # Movies/series tracking
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
- `/birthdays` - Birthday reminders with relationship tracking
- `/watchlist` - Movies/series tracking with progress
- `/settings` - Account and modular data management