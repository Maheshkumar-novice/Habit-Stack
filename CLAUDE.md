# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HabitStack is a cross-platform daily habit tracker built with Flask, Tailwind CSS and Python 3.13. It provides a beautiful responsive web interface with reliable form-based interactions, perfect for mobile and desktop use. The application follows a simple, maintainable architecture without JavaScript frameworks.

## Development Commands

**IMPORTANT: Always use `uv` for Python package management and running commands.**

**Run the HabitStack web application:**
```bash
uv run python app.py
```

**Install dependencies:**
```bash
uv sync
```

**Add new dependencies:**
```bash
uv add <package-name>
```

**Add development dependencies:**
```bash
uv add --dev <package-name>
```

**Testing with timeout (useful for debugging):**
```bash
timeout 10 uv run python app.py
```

**Access the application:**
- Web interface: http://localhost:8000/habitstack/
- All routes are prefixed with `/habitstack/`
- PWA installation available on mobile devices

## Project Structure

### Core Application Files
- `app.py` - Main Flask application and configuration (64 lines)
- `database.py` - Connection pooling and encryption infrastructure with all tables (242 lines)
- `utils.py` - Validation helpers and decorators (41 lines)

### Encryption Infrastructure
- `utils/encryption.py` - AES-128 field-level encryption utilities with PBKDF2 key derivation (120 lines)
- `utils/field_registry.py` - Dynamic field registration system for encryptable data (45 lines)
- `utils/preferences.py` - User encryption preference management with smart defaults (80 lines)
- `models/base_encrypted.py` - Encryption mixin for all data models (85 lines)

### Modular Blueprint Architecture
- `auth.py` - Authentication routes and handlers (61 lines)
- `habits.py` - Habit management routes (112 lines)
- `notes.py` - Daily notes functionality (69 lines)
- `todos.py` - Todo list management routes (118 lines)
- `reading.py` - Reading list management routes (195 lines)
- `birthdays.py` - Birthday reminder routes (142 lines)
- `watchlist.py` - Movies/series watchlist routes (205 lines)
- `sports.py` - Sports news aggregation and caching (279 lines)
- `settings.py` - Data management and account settings (290 lines)

### Data Models (Modular Architecture with Encryption)
- `models/` - Modular model package with field-level encryption support (1500+ total lines)
  - `models/__init__.py` - Package exports and documentation (19 lines)
  - `models/user.py` - User authentication and account management (110 lines)
  - `models/habit.py` - Habit tracking with encrypted name/description fields (273 lines)
  - `models/note.py` - Daily journaling with encrypted content (113 lines)
  - `models/todo.py` - Todo management with encrypted title/description/category (273 lines)
  - `models/reading.py` - Reading list with encrypted notes field (245 lines)
  - `models/birthday.py` - Birthday reminders with encrypted name/notes (147 lines)
  - `models/watchlist.py` - Movies/series tracking with encrypted notes (220 lines)
  - `models/sports.py` - Sports news caching and management (165 lines)
  - `models/data_manager.py` - Data export/import with encryption awareness (585 lines)
  - `models/base_encrypted.py` - Encryption mixin providing encryption/decryption methods (85 lines)

### Templates (Responsive UI)
- `templates/` - Jinja2 HTML templates with form-based interactions
  - `base.html` - Base template with Tailwind CSS and PWA setup
  - `navbar.html` - Unified responsive navigation component with hamburger menu
  - `dashboard.html` - Main habit tracking dashboard
  - `manage_habits.html` - Habits management interface
  - `add_habit_page.html` - Dedicated add habit page
  - `edit_habit_page.html` - Dedicated edit habit page
  - `notes.html` - Daily notes journaling interface
  - `todos.html` - Todo list management with smart organization
  - `add_todo_page.html` - Add todo form page
  - `edit_todo_page.html` - Edit todo form page
  - `reading.html` - Reading list main page with status-based organization
  - `add_book_page.html` - Add book form page
  - `edit_book_page.html` - Edit book form page
  - `birthdays.html` - Birthday reminders main page
  - `add_birthday_page.html` - Add birthday form page
  - `edit_birthday_page.html` - Edit birthday form page
  - `watchlist.html` - Movies/series watchlist main page
  - `add_movie_page.html` - Add movie/series form page
  - `edit_movie_page.html` - Edit movie/series form page
  - `sports.html` - Sports news aggregation interface with multi-source display
  - `settings.html` - Comprehensive settings and data management page with mobile optimization
  - `landing.html` - Marketing landing page showcasing all features
  - `login.html` / `signup.html` - Authentication pages
  - `habits_container.html` - Habit cards grid component
  - `habit_card.html` - Individual habit card component
  - `points_display.html` - Points counter component

### Supporting Files
- `static/` - PWA assets (manifest, service worker, icons)
- `pyproject.toml` - Python project configuration and dependencies
- `habitstack.db` - SQLite database (auto-created on first run)
- `.python-version` - Specifies Python 3.13 requirement
- `DEPLOYMENT.md` - Complete production deployment guide

## Architecture Notes

**Current Implementation:**
- Pure Flask backend with modular Blueprint architecture
- Standard HTML form submissions with server-side redirects
- Tailwind CSS for responsive design (CDN-based, no build step)
- SQLite database with proper user isolation and soft delete capability
- Session-based authentication with bcrypt password hashing
- Progressive Web App (PWA) capabilities
- Minimal JavaScript (only PWA service worker and hamburger menu)

**Database Schema:**
- `users` - User accounts with bcrypt password hashing, encryption salt, and soft delete support
- `habits` - User's custom habits with encrypted names/descriptions, points and completion tracking  
- `habit_completions` - Daily completion tracking with date constraints
- `daily_notes` - User's daily journaling with encrypted content and date-based organization
- `todos` - Task management with encrypted titles/descriptions/categories, priorities, due dates, and soft delete
- `reading_list` - Book tracking with progress, status, ratings, and encrypted personal notes
- `birthdays` - Birthday reminders with encrypted names/notes, relationship types and dates
- `watchlist` - Movies/series tracking with encrypted notes, status, progress, and ratings
- `sports_news` - Football transfer news caching with multi-source aggregation
- `encryptable_fields` - Registry of all encryptable fields across the application
- `user_encryption_preferences` - User-specific encryption choices for granular control

**Database Optimizations:**
- SQLite with WAL mode for better concurrency
- Connection pooling (max 10 connections) for performance
- Optimized indexes on frequently queried columns including soft delete
- 10MB cache size for faster query execution
- Automatic schema migrations for backward compatibility

**Navigation Architecture:**
- Unified `navbar.html` component used across all pages
- Responsive hamburger menu for mobile with slide-out drawer
- Desktop horizontal navigation with proper spacing
- Visual indicators for current page highlighting
- User profile section in mobile menu with avatar

## Route Structure (All prefixed with `/habitstack/`)

### Main Interface
- `/` - Redirects to `/habitstack/`
- `/habitstack/` - Dashboard (main habit tracking interface)

### Authentication
- `/habitstack/login` - User login
- `/habitstack/signup` - User registration with password strength validation
- `/habitstack/logout` - User logout

### Habit Management
- `/habitstack/habits` - Habits management page
- `/habitstack/add-habit-page` - Add new habit form page
- `/habitstack/add-habit` (POST) - Create habit handler
- `/habitstack/edit-habit-page/<id>` - Edit habit form page
- `/habitstack/edit-habit/<id>` (POST) - Update habit handler
- `/habitstack/delete-habit/<id>` (POST) - Delete habit handler
- `/habitstack/toggle-habit/<id>` (POST) - Toggle habit completion

### Daily Notes
- `/habitstack/notes` - Today's notes (default)
- `/habitstack/notes/<date>` - View/edit notes for specific date
- `/habitstack/notes/<date>/save` (POST) - Save note for date
- `/habitstack/notes/<date>/delete` (POST) - Delete note for date

### Todo List Management
- `/habitstack/todos` - Todo list main page with smart organization
- `/habitstack/add-todo-page` - Add new todo form page
- `/habitstack/add-todo` (POST) - Create todo handler
- `/habitstack/edit-todo-page/<id>` - Edit todo form page
- `/habitstack/edit-todo/<id>` (POST) - Update todo handler
- `/habitstack/delete-todo/<id>` (POST) - Delete todo handler
- `/habitstack/toggle-todo/<id>` (POST) - Toggle todo completion

### Reading List Management
- `/habitstack/reading` - Reading list main page organized by status
- `/habitstack/add-book-page` - Add new book form page
- `/habitstack/add-book` (POST) - Create book handler
- `/habitstack/edit-book-page/<id>` - Edit book form page
- `/habitstack/edit-book/<id>` (POST) - Update book handler
- `/habitstack/delete-book/<id>` (POST) - Delete book handler
- `/habitstack/mark-reading/<id>` (POST) - Mark book as currently reading
- `/habitstack/mark-book-completed/<id>` (POST) - Mark book as completed
- `/habitstack/update-book-progress/<id>` (POST) - Update reading progress

### Birthday Reminders
- `/habitstack/birthdays` - Birthday reminders main page
- `/habitstack/add-birthday-page` - Add new birthday form page
- `/habitstack/add-birthday` (POST) - Create birthday handler
- `/habitstack/edit-birthday-page/<id>` - Edit birthday form page
- `/habitstack/edit-birthday/<id>` (POST) - Update birthday handler
- `/habitstack/delete-birthday/<id>` (POST) - Delete birthday handler

### Movies/Series Watchlist
- `/habitstack/watchlist` - Watchlist main page organized by status
- `/habitstack/add-movie-page` - Add movie/series form page
- `/habitstack/add-movie` (POST) - Create watchlist item handler
- `/habitstack/edit-movie-page/<id>` - Edit movie/series form page
- `/habitstack/edit-movie/<id>` (POST) - Update watchlist item handler
- `/habitstack/delete-movie/<id>` (POST) - Delete watchlist item handler
- `/habitstack/mark-completed/<id>` (POST) - Mark item as completed
- `/habitstack/update-episode/<id>` (POST) - Update episode progress

### Sports News Aggregation
- `/habitstack/sports` - Sports news main page with multi-source display
- `/habitstack/sports/refresh` (POST) - Refresh news from all sources
- `/habitstack/sports/clear` (POST) - Clear cached articles

### Settings & Data Management
- `/habitstack/settings` - Comprehensive settings page with mobile optimization and encryption preferences
- `/habitstack/update-encryption-preferences` (POST) - Update user encryption field preferences
- `/habitstack/export` (POST) - Export all user data as JSON (legacy)
- `/habitstack/export-modules` (POST) - Export selected modules as JSON with decrypted data
- `/habitstack/import` (POST) - Import user data from JSON file (legacy)
- `/habitstack/import-modules` (POST) - Import selected modules from JSON
- `/habitstack/analyze-import` (POST) - Analyze import file contents
- `/habitstack/update-password` (POST) - Update user password
- `/habitstack/delete-account` (POST) - Soft delete user account

## Key Features

### User Experience
- Beautiful, mobile-first responsive design with hamburger navigation
- Simple form-based interactions with immediate feedback
- Dedicated pages for all management functions (no modals)
- Reliable navigation with explicit routing
- Instant visual feedback through page reloads
- Professional user profile display in mobile menu

### Authentication & Security
- Username/password authentication (no email required)
- Password strength validation with visual feedback
- Session-based authentication with secure cookies
- **Zero-Knowledge Privacy Architecture** - User-controlled field-level encryption
- **AES-128 Encryption** with PBKDF2 key derivation (100,000 iterations)
- **Granular Encryption Control** - Users choose which personal data fields to encrypt
- **Admin Cannot Read Encrypted Data** - True privacy protection at database level
- User data isolation and privacy protection
- CSRF protection through Flask forms
- Soft delete functionality for account management
- Secure password update with current password verification

### Habit Tracking
- Daily habit completion tracking
- Streak calculation with fire emoji indicators 🔥
- Points system for gamification with daily totals
- Habit statistics (total completions, last completed)
- Responsive card-based layout

### Daily Notes & Journaling
- Dedicated notes section separate from habit tracking
- Date-based navigation (Previous/Next/Today)
- Large textarea for comfortable writing
- Manual save functionality (no autosave)
- Recent notes history with previews
- Complete user data isolation

### Todo List Management
- Smart organization by status (overdue, today, upcoming, someday, completed)
- Priority levels with visual color coding (high, medium, low)
- Due date tracking with overdue highlighting
- Category system for task organization
- Progress statistics and completion tracking
- Full CRUD operations with dedicated form pages
- Mobile-optimized responsive design

### Reading List Management
- Status-based organization (Want to Read, Currently Reading, Completed)
- Progress tracking with current page/total pages and percentage calculation
- 5-star rating system for completed books with visual indicators
- Personal notes for each book with rich textarea editing
- Quick action buttons for status changes and progress updates
- Comprehensive statistics dashboard with reading metrics
- Mobile-responsive design with intuitive book management

### Birthday Reminders
- Today's birthdays with special highlighting
- Upcoming birthdays with countdown (next 30 days)
- Relationship type categorization (Family, Friend, Colleague, etc.)
- Personal notes for each birthday
- Smart date calculations for year transitions
- Clean management interface with full CRUD operations

### Movies/Series Watchlist
- Status-based organization (Want to Watch, Currently Watching, Completed)
- Episode progress tracking for TV series
- Genre categorization and priority levels
- Star rating system for completed items
- Quick episode update functionality
- Comprehensive statistics dashboard
- Support for movies, series, documentaries, anime, and mini-series

### Sports News Aggregation
- Multi-source football transfer news fetching (BBC Sport, Sky Sports, Goal.com, Reddit r/soccer)
- Intelligent article caching with 3-day retention and duplicate prevention
- Real-time news refresh with user-friendly status updates
- Responsive mobile-first interface with source-based organization
- Article statistics and last update tracking
- Manual cache management with clear functionality
- Error handling with graceful degradation

### Data Management & Settings
- **User-Controlled Encryption** - Granular field-level encryption preferences with UI control
- **Privacy Level Indicators** - Visual feedback on encryption coverage (None/Basic/Enhanced/Maximum)
- **Zero-Knowledge Architecture** - Admin cannot read encrypted user data from database
- **Dynamic Field Registry** - Automatic discovery of encryptable fields for new features
- **Smart Encryption Defaults** - Privacy-focused suggestions based on field sensitivity
- **Modular Data Export** - Select specific modules to export with live counts (always decrypted)
- **Complete JSON Export** - Download all user data with timestamp
- **Modular Data Import** - Choose which modules to import with strategies
- **Full Data Import** - Replace all data from backup file with validation
- **File Analysis** - Preview import file contents before importing
- **Data Portability** - JSON format for migration and analysis
- **Password Management** - Secure password updates with strength validation
- **Account Deletion** - Professional soft delete with multiple safeguards
- **Mobile Optimization** - Fully responsive settings interface
- **Backup Recommendations** - Clear warnings and export reminders
- **Safety Features** - Double confirmation for destructive actions

### Technical Features
- **Field-Level Encryption** - AES-128 with user-derived keys for sensitive data protection
- **Session-Based Key Management** - Encryption keys derived from user passwords at login
- **OWASP-Compliant Security** - 100,000 PBKDF2 iterations with secure salt generation
- **Backward Compatibility** - Seamless operation with existing unencrypted data
- Progressive Web App (PWA) for mobile installation
- Service worker for offline capability
- Responsive design that works on all screen sizes
- No build system required - runs on single Python server
- Form validation and error handling
- Modular architecture for maintainability

## Development Patterns

### Form Handling
- All interactions use standard HTML forms with POST methods
- Server-side validation and error handling
- Explicit redirects after successful operations
- Flash messages for user feedback with proper categorization

### Navigation Pattern
- Dashboard: View and complete habits (primary focus)
- Habits: Add, edit, delete, and organize habits
- Notes: Daily journaling and reflection
- Todos: Task management with smart organization
- Reading: Book tracking and reading progress management
- Birthdays: Birthday reminders and relationship tracking
- Watchlist: Movies/series entertainment tracking
- Sports: Football transfer news aggregation and reading
- Settings: Data management and account preferences
- Clear separation of all features with consistent navigation

### Database Operations
- Context managers for proper connection handling
- User ownership verification on all operations
- Proper error handling and validation
- Foreign key constraints for data integrity
- Soft delete implementation for data preservation

### Responsive Design
- Mobile-first approach with Tailwind CSS
- Breakpoint usage: `sm:` (640px+) for tablet/desktop
- Touch-friendly button sizes and spacing
- Readable text scaling across devices
- Hamburger menu for mobile navigation

### Code Organization
- Modular Blueprint architecture for feature separation
- Unified model package with focused responsibilities
- Centralized navigation component for consistency
- Clean separation of concerns across layers

## Production Deployment

See `DEPLOYMENT.md` for complete production deployment guide including:
- Gunicorn configuration
- Nginx reverse proxy setup
- systemd service configuration
- SSL setup with Certbot
- Monitoring and maintenance procedures

## Development Notes

### Code Style
- Follow existing patterns for consistency
- Use proper Jinja2 templating conventions
- Maintain responsive design principles
- Keep forms simple and accessible
- Follow modular architecture patterns

### Testing
- Test all form submissions end-to-end
- Verify responsive design on different screen sizes  
- Check authentication flows and user isolation
- Validate habit tracking logic and streak calculations
- **Test encryption/decryption workflows** - Verify field-level encryption across all models
- **Validate encryption preference changes** - Test preference updates and data migration
- **Check encryption key management** - Verify session-based key derivation and storage
- Test data export/import workflows with encryption awareness
- Verify soft delete functionality

### Common Issues to Check
- Ensure all routes are prefixed with `/habitstack/`
- Verify form action URLs are correct
- Check user authentication on protected routes
- **Verify encryption key availability** - Check session contains encryption_key for encrypted operations
- **Test encrypted field handling** - Ensure all model methods properly encrypt/decrypt data
- **Validate encryption preferences** - Check user preferences are applied correctly
- Test navigation between pages works correctly
- Validate responsive design on mobile devices
- Ensure data export before account deletion

## Recent Major Updates

### User-Controlled Field Encryption System (Latest)
- **Implemented Zero-Knowledge Privacy Architecture** - Admin cannot read encrypted user data
- **Added AES-128 Field-Level Encryption** with PBKDF2 key derivation (100,000 iterations)
- **Created User-Controlled Granular Encryption** - Users choose which fields to encrypt via UI
- **Built Dynamic Field Registry System** - Automatic discovery of 10 encryptable fields across 6 modules
- **Added Encryption Preference Management** - Smart defaults and privacy level indicators
- **Updated All Model Methods** - 273+ lines of encryption/decryption logic across all data models
- **Enhanced Settings UI** - Module-grouped field selection with live privacy feedback
- **Session-Based Key Management** - Encryption keys derived from user login passwords
- **Backward Compatibility** - Seamless operation with existing unencrypted data
- **Export/Import Awareness** - Always exports decrypted data for portability
- **Database Schema Extensions** - Added encryption_salt, encryptable_fields, user_encryption_preferences tables
- **OWASP-Compliant Security** - Industry-standard cryptographic practices
- **Comprehensive Testing** - All model updates verified and application tested

### Sports News Aggregation Feature (Latest)
- Added comprehensive football transfer news aggregation from multiple sources
- Implemented BBC Sport RSS feed, Sky Sports web scraping, Goal.com parsing, and Reddit r/soccer API integration
- Created intelligent article caching system with 3-day retention and duplicate prevention
- Built responsive sports.html interface with source-based organization and mobile-first design
- Added sports navigation to both desktop and mobile interfaces with soccer ball emoji
- Created SportsNews model for efficient article management and database operations
- Added sports_news table with proper indexing and created_at timestamps
- Integrated sports blueprint into main Flask application with proper URL routing
- Added required web scraping dependencies: requests, beautifulsoup4, feedparser, lxml, rich
- Consolidated all functionality into self-contained sports module (removed external news.py dependency)
- Implemented refresh/clear functionality with user-friendly flash messages and error handling
- Added 279+ lines of sports news aggregation functionality

### Reading List Feature Integration
- Added comprehensive book tracking functionality following watchlist patterns
- Created status-based organization (Want to Read, Currently Reading, Completed)
- Implemented progress tracking with current page/total pages and percentage calculation
- Built 5-star rating system for completed books with visual indicators
- Added personal notes for each book with rich textarea editing
- Created quick action buttons for status changes and progress updates
- Built comprehensive statistics dashboard with reading metrics
- Integrated reading into modular data export/import system
- Added reading navigation to both desktop and mobile interfaces
- Created dedicated form pages for book CRUD operations
- Added 198+ lines of reading management functionality

### Mobile Responsiveness Optimization
- Enhanced settings page with comprehensive mobile optimization
- Improved container padding and spacing for small screens  
- Made module selection grids responsive (1 column mobile, 2 desktop)
- Converted button layouts to stack vertically on mobile
- Added full-width buttons with proper touch targets
- Enhanced icon sizing and text truncation for mobile devices
- Optimized form elements and input fields for mobile use

### Todo List Feature Integration
- Added comprehensive todo list management functionality
- Created smart organization by status (overdue, today, upcoming, someday, completed)
- Implemented priority levels with visual color coding
- Built due date tracking with overdue highlighting
- Added category system for task organization
- Created dedicated form pages for todo CRUD operations
- Integrated todos into modular data export/import system
- Added 205+ lines of todo management functionality

### Modular Data Export/Import System
- Built comprehensive module selection interface for exports/imports
- Added live data counts for each module during selection
- Implemented file analysis for import preview functionality
- Created import strategies (replace vs merge) for flexible data handling
- Enhanced data validation for both modular and legacy exports
- Added robust error handling and user feedback systems
- Extended data manager with 245+ lines of modular functionality

### Comprehensive Account Management
- Added password update functionality with current password verification
- Implemented soft delete account system with data preservation
- Created professional danger zone UI with multiple confirmation layers
- Enhanced settings page with complete account management features
- Added 316+ lines of security and account management functionality

### Navigation Architecture Refactoring
- Split monolithic 653-line models.py into focused modular packages
- Created unified navbar.html component for consistency
- Implemented responsive hamburger menu for mobile
- Added user profile section to mobile navigation
- Enhanced mobile UX with cleaner header layout

### Entertainment Watchlist Feature
- Added comprehensive movies/series tracking functionality
- Created status-based organization (Want to Watch, Currently Watching, Completed)
- Implemented episode progress tracking for TV series
- Built statistics dashboard and quick action functionality
- Integrated watchlist navigation across all pages

### Birthday Reminders Feature
- Added birthday tracking functionality for relationship management
- Created today's birthdays highlighting and upcoming countdown
- Implemented relationship types and personal notes
- Smart date handling for year transitions and recurring birthdays
- Integrated birthday navigation across all pages

### Daily Notes Feature
- Added dedicated daily notes functionality for user journaling
- Created date-based navigation with Previous/Next/Today
- Implemented manual save functionality with recent notes history
- Built responsive notes interface with large textarea
- Integrated notes into main navigation across all pages

### SQLite & Architecture Optimizations
- Enabled WAL mode for better concurrent read/write performance
- Implemented connection pooling (max 10 connections)
- Added database indexes for frequently queried columns
- Optimized cache size (10MB) and synchronization settings
- Split monolithic application into modular Blueprint architecture

This creates HabitStack as a comprehensive personal life organizer with eight core features: habit tracking, daily notes, todo list management, reading list management, birthday reminders, entertainment watchlist, sports news aggregation, and data management - all enhanced with user-controlled field-level encryption for maximum privacy. The application provides a maintainable, reliable, secure, and universally compatible web experience with enterprise-level account management capabilities, zero-knowledge privacy architecture, and optimized mobile responsiveness.