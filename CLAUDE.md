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

- `app.py` - Flask backend with all routes and database logic
- `templates/` - Jinja2 HTML templates with form-based interactions
  - `base.html` - Base template with Tailwind CSS and PWA setup
  - `dashboard.html` - Main habit tracking dashboard
  - `manage_habits.html` - Habits management interface
  - `add_habit_page.html` - Dedicated add habit page
  - `edit_habit_page.html` - Dedicated edit habit page
  - `landing.html` - Marketing landing page
  - `login.html` / `signup.html` - Authentication pages
  - `habits_container.html` - Habit cards grid component
  - `habit_card.html` - Individual habit card component
  - `points_display.html` - Points counter component
- `static/` - PWA assets (manifest, service worker, icons)
- `pyproject.toml` - Python project configuration and dependencies
- `habitstack.db` - SQLite database (auto-created on first run)
- `.python-version` - Specifies Python 3.13 requirement
- `DEPLOYMENT.md` - Complete production deployment guide

## Architecture Notes

**Current Implementation (Post-HTMX Removal):**
- Pure Flask backend with Jinja2 templating
- Standard HTML form submissions with server-side redirects
- Tailwind CSS for responsive design (CDN-based, no build step)
- SQLite database with proper user isolation
- Session-based authentication with bcrypt password hashing
- Progressive Web App (PWA) capabilities
- Zero JavaScript dependencies (except PWA service worker)

**Database Schema:**
- `users` - User accounts with bcrypt password hashing
- `habits` - User's custom habits with points and descriptions  
- `habit_completions` - Daily completion tracking with date constraints

**Route Structure (All prefixed with `/habitstack/`):**
- `/` - Redirects to `/habitstack/`
- `/habitstack/` - Dashboard (main habit tracking interface)
- `/habitstack/login` - User login
- `/habitstack/signup` - User registration with password strength validation
- `/habitstack/logout` - User logout
- `/habitstack/habits` - Habits management page
- `/habitstack/add-habit-page` - Add new habit form page
- `/habitstack/add-habit` (POST) - Create habit handler
- `/habitstack/edit-habit-page/<id>` - Edit habit form page
- `/habitstack/edit-habit/<id>` (POST) - Update habit handler
- `/habitstack/delete-habit/<id>` (POST) - Delete habit handler
- `/habitstack/toggle-habit/<id>` (POST) - Toggle habit completion

## Key Features

**User Experience:**
- Beautiful, mobile-first responsive design
- Simple form-based interactions with immediate feedback
- Dedicated pages for habit management (no modals)
- Reliable navigation with explicit routing
- Instant visual feedback through page reloads

**Authentication & Security:**
- Username/password authentication (no email required)
- Password strength validation with visual feedback
- Session-based authentication with secure cookies
- User data isolation and privacy protection
- CSRF protection through Flask forms

**Habit Tracking:**
- Daily habit completion tracking
- Streak calculation with fire emoji indicators 🔥
- Points system for gamification with daily totals
- Habit statistics (total completions, last completed)
- Responsive card-based layout

**Technical Features:**
- Progressive Web App (PWA) for mobile installation
- Service worker for offline capability
- Responsive design that works on all screen sizes
- No build system required - runs on single Python server
- Form validation and error handling

## Development Patterns

**Form Handling:**
- All interactions use standard HTML forms with POST methods
- Server-side validation and error handling
- Explicit redirects after successful operations
- Flash messages for user feedback

**Navigation Pattern:**
- Dashboard: View and complete habits
- Manage Habits: Add, edit, delete, and organize habits
- Clear separation of daily tracking vs management

**Database Operations:**
- Context managers for proper connection handling
- User ownership verification on all operations
- Proper error handling and validation
- Foreign key constraints for data integrity

**Responsive Design:**
- Mobile-first approach with Tailwind CSS
- Breakpoint usage: `sm:` (640px+) for tablet/desktop
- Touch-friendly button sizes and spacing
- Readable text scaling across devices

## Production Deployment

See `DEPLOYMENT.md` for complete production deployment guide including:
- Gunicorn configuration
- Nginx reverse proxy setup
- systemd service configuration
- SSL setup with Certbot
- Monitoring and maintenance procedures

## Development Notes

**Code Style:**
- Follow existing patterns for consistency
- Use proper Jinja2 templating conventions
- Maintain responsive design principles
- Keep forms simple and accessible

**Testing:**
- Test all form submissions end-to-end
- Verify responsive design on different screen sizes  
- Check authentication flows and user isolation
- Validate habit tracking logic and streak calculations

**Common Issues to Check:**
- Ensure all routes are prefixed with `/habitstack/`
- Verify form action URLs are correct
- Check user authentication on protected routes
- Test navigation between pages works correctly
- Validate responsive design on mobile devices

## Recent Changes

**Major Architecture Change (Latest):**
- Completely removed HTMX dependency for better reliability
- Converted all modal interactions to dedicated pages
- Replaced AJAX calls with standard form submissions
- Simplified JavaScript to only PWA service worker registration
- Fixed navigation reliability issues with explicit routing
- Reduced bundle size by ~50KB (no HTMX)

This creates a more maintainable, reliable, and universally compatible web application that works consistently across all browsers and devices.