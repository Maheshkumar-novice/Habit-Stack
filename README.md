# HabitStack

A clean, fast, and reliable daily habit tracker built with Flask and modern web technologies. Track your habits, build streaks, and form lasting routines with a beautiful mobile-first interface.

## ✨ Features

### 🎯 **Habit Tracking**
- Daily habit completion tracking with visual feedback
- Streak counting with fire emoji indicators 🔥
- Points system for gamification and motivation
- Clean card-based interface for easy interaction

### 🔐 **Simple Authentication**
- Username/password authentication (no email required)
- Secure password hashing with bcrypt
- Session-based authentication with proper security
- User data isolation and privacy protection

### 📱 **Mobile-First Design**
- Responsive design that works perfectly on all devices
- Progressive Web App (PWA) for native-like mobile experience
- Touch-optimized interactions and button sizing
- Install on mobile devices like a native app

### ⚡ **Performance & Reliability**
- SQLite with WAL mode for better concurrency
- Connection pooling for optimized database performance
- Form-based interactions for universal compatibility
- No JavaScript dependencies (except PWA service worker)

## 🚀 Quick Start

### Prerequisites
- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd habitstack

# Install dependencies
uv sync

# Run the application
uv run python app.py

# Visit http://localhost:8000/habitstack/
```

The application will automatically:
- Initialize the SQLite database
- Enable WAL mode for better performance
- Create necessary tables and indexes
- Start the development server on port 8000

### First Use

1. Navigate to `http://localhost:8000/habitstack/`
2. Click "Get Started" to create an account
3. Create your username and password
4. Start adding habits and tracking your progress!

## 🏗️ Architecture

### **Modular Design**
HabitStack follows a clean, modular architecture for maintainability:

```
├── app.py              # Main Flask application (56 lines)
├── models.py           # User & Habit data models (251 lines)
├── database.py         # Connection pooling & optimization (185 lines)
├── auth.py             # Authentication routes (60 lines)
├── habits.py           # Habit management routes (110 lines)
├── utils.py            # Validation & helpers (40 lines)
└── templates/          # Jinja2 HTML templates
```

### **Database Schema**
- **users** - User accounts with bcrypt password hashing
- **habits** - User's custom habits with points and descriptions
- **habit_completions** - Daily completion tracking with date constraints

### **Key Optimizations**
- **WAL Mode**: Write-Ahead Logging for concurrent read/write operations
- **Connection Pooling**: Reusable database connections for better performance
- **Indexes**: Optimized queries for habit lookups and streak calculations
- **Clean Architecture**: Separation of concerns for easy maintenance

## 🛠️ Technology Stack

### **Backend**
- **Flask** - Lightweight Python web framework
- **SQLite** - Embedded database with WAL mode
- **bcrypt** - Secure password hashing
- **Python 3.13** - Latest Python features and performance

### **Frontend**
- **Tailwind CSS** - Utility-first CSS framework (CDN)
- **Jinja2** - Template engine for dynamic HTML
- **Progressive Web App** - Service worker for offline capability
- **Form-based interactions** - No JavaScript frameworks required

### **Development**
- **uv** - Fast Python package manager
- **No build step** - Direct development without compilation
- **Hot reload** - Automatic server restart during development

## 📋 Development Commands

```bash
# Development server
uv run python app.py

# Install new dependencies
uv add <package-name>

# Add development dependencies
uv add --dev <package-name>

# Sync dependencies
uv sync

# Testing with timeout (useful for debugging)
timeout 10 uv run python app.py
```

## 🔧 Configuration

### **Environment Variables**
- `SECRET_KEY` - Flask secret key (production)
- `DEBUG` - Enable debug mode (development only)

### **Database Settings**
The application uses SQLite with the following optimizations:
- **WAL mode** enabled for better concurrency
- **Connection pooling** (max 10 connections)
- **10MB cache size** for faster queries
- **Indexes** on frequently queried columns

## 📱 Progressive Web App

HabitStack includes PWA capabilities:
- **Offline support** via service worker
- **Mobile installation** - Add to home screen
- **Native-like experience** on mobile devices
- **Responsive design** across all screen sizes

To install on mobile:
1. Visit the app in your mobile browser
2. Look for "Add to Home Screen" prompt
3. Confirm installation
4. Launch like a native app

## 🚦 Routes

All routes are prefixed with `/habitstack/`:

### **Authentication**
- `GET/POST /habitstack/login` - User login
- `GET/POST /habitstack/signup` - User registration
- `GET /habitstack/logout` - User logout

### **Main Interface**
- `GET /habitstack/` - Dashboard (main habit tracking)
- `GET /habitstack/habits` - Habits management page

### **Habit Management**
- `GET /habitstack/add-habit-page` - Add new habit form
- `POST /habitstack/add-habit` - Create habit handler
- `GET /habitstack/edit-habit-page/<id>` - Edit habit form
- `POST /habitstack/edit-habit/<id>` - Update habit handler
- `POST /habitstack/delete-habit/<id>` - Delete habit handler
- `POST /habitstack/toggle-habit/<id>` - Toggle habit completion

## 🎨 Design Principles

### **Simplicity First**
- Clean, minimal interface without clutter
- Form-based interactions for universal compatibility
- No unnecessary animations or complex JavaScript

### **Mobile-First**
- Touch-friendly button sizes and spacing
- Responsive breakpoints: `sm:` (640px+) for tablet/desktop
- Progressive enhancement for larger screens

### **Reliability**
- Standard HTML forms with server-side processing
- Graceful degradation when JavaScript is disabled
- Consistent behavior across all browsers and devices

## 🚀 Deployment

See [`DEPLOYMENT.md`](DEPLOYMENT.md) for complete production deployment guide including:
- Gunicorn configuration
- Nginx reverse proxy setup
- systemd service configuration
- SSL setup with Certbot
- Monitoring and maintenance procedures

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### **Development Guidelines**
- Follow existing code patterns and architecture
- Use proper Jinja2 templating conventions
- Maintain responsive design principles
- Keep forms simple and accessible
- Add tests for new functionality

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🏆 Why HabitStack?

- **No vendor lock-in** - Self-hosted with full data control
- **Privacy-focused** - Your data stays on your server
- **Lightweight** - Runs on minimal resources
- **Maintainable** - Clean, well-documented codebase
- **Extensible** - Easy to customize and enhance

Built for developers who want a reliable, self-hosted habit tracker without the complexity of modern JavaScript frameworks.

---

*Track your habits, build your future.* 🚀