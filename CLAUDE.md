# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

HabitStack is a cross-platform daily habit tracker built with Flask, HTMX, Tailwind CSS and Python 3.13. It provides a beautiful responsive web interface with smooth interactions, perfect for mobile and desktop.

## Development Commands

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

**Access the application:**
- Web interface: http://localhost:8000/habitstack/
- PWA installation available on mobile devices

## Project Structure

- `app.py` - Flask backend with routes and database logic
- `templates/` - Jinja2 HTML templates with HTMX interactions
- `static/` - PWA assets (manifest, service worker, icons)
- `pyproject.toml` - Python project configuration and dependencies
- `habitstack.db` - SQLite database (auto-created on first run)
- `.python-version` - Specifies Python 3.13 requirement

## Architecture Notes

**Current Implementation:**
- Flask backend with Jinja2 templating
- HTMX for smooth frontend interactions (no build step)
- Tailwind CSS for beautiful responsive design
- SQLite database with user accounts and habit tracking
- Session-based authentication with flash messages

**Database Schema:**
- `users` - User accounts with bcrypt password hashing
- `habits` - User's custom habits with points and descriptions
- `habit_completions` - Daily completion tracking

**Key Features:**
- Beautiful, mobile-first UI with Tailwind CSS
- Smooth HTMX interactions without page reloads
- Simple username/password authentication with strength validation
- Daily habit checking with instant visual feedback
- Streak tracking with fire emoji indicators 🔥
- Points system for gamification
- Modal forms for adding habits
- Progressive Web App (PWA) for mobile installation
- User isolation and privacy

**UI Highlights:**
- Professional gradient landing page
- Card-based habit layout with hover effects
- Instant toggle animations
- Mobile-optimized touch interactions
- No build system required - runs on single Python server