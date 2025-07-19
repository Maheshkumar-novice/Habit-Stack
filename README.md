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

## User-Controlled Field Encryption

HabitStack implements a comprehensive zero-knowledge encryption system that gives users granular control over which personal data fields are encrypted. The system uses industry-standard cryptographic practices to ensure that sensitive data remains protected while maintaining usability.

### Encryption Overview

- **Zero-Knowledge Architecture**: The server cannot read encrypted user data
- **Field-Level Granularity**: Users choose exactly which fields to encrypt
- **Session-Based Keys**: Encryption keys derived from passwords, stored only in session
- **Smart Migration**: Automatic encryption/decryption when preferences change
- **Privacy Levels**: Recommended encryption settings based on data sensitivity

### Cryptographic Implementation

**Key Derivation**: PBKDF2-HMAC-SHA256 with 100,000 iterations (OWASP compliant)
- Password + 16-byte user salt → 32-byte encryption key
- Salt generated once per user, stored in database
- Keys derived fresh each login, stored only in session

**Encryption**: Fernet (AES-128 in CBC mode with HMAC authentication)
- Authenticated encryption prevents tampering
- Built-in timestamp validation
- URL-safe base64 encoding for database storage

**Data Detection**: Smart identification of encrypted vs plaintext data
- Fernet tokens start with 'gAAAAA' (timestamp marker)
- Length and base64 validation checks
- Graceful fallback for mixed data states

### Encryptable Fields

| Module | Field | Privacy Level | Recommendation |
|--------|-------|---------------|----------------|
| **Habits** | name | Medium | Optional - visible on dashboard |
| | description | Medium | Optional - usually brief |
| **Notes** | content | High | **Recommended** - personal thoughts |
| **Todos** | title | Medium | Optional - often task-oriented |
| | description | High | **Recommended** - detailed plans |
| **Reading** | title | Low | Optional - book titles usually public |
| | notes | High | **Recommended** - personal reviews |
| **Birthdays** | name | High | **Recommended** - personal relationships |
| | notes | High | **Recommended** - relationship details |
| **Watchlist** | title | Low | Optional - entertainment titles |
| | notes | Medium | Optional - viewing preferences |

### Privacy Levels

- **High (Recommended)**: Personal thoughts, relationships, detailed plans
- **Medium (Optional)**: Descriptive content, personal preferences  
- **Low (Not recommended)**: Titles, brief labels, public information

### Technical Files

- `utils/encryption.py` - Core encryption/decryption operations (111 lines)
- `utils/field_registry.py` - Central field definitions and metadata
- `utils/preferences.py` - User preference management and smart defaults
- `utils/migration.py` - Automatic data encryption/decryption system
- `auth.py:setup_user_encryption_key()` - Session key derivation and storage

### Security Features

- **Session Security**: Keys cleared on logout, regenerated on login
- **Migration Safety**: Existing data preserved during preference changes
- **Error Handling**: Graceful fallback prevents data loss
- **Production Ready**: Database schema auto-migration for deployment