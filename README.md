# Flask Application

A modern Flask web application with session-based authentication, SQLite database, and beautiful Tailwind CSS styling.

## Features

- **Session-based Authentication**: Secure login/logout functionality with password hashing
- **SQLite Database**: Lightweight database with SQLAlchemy ORM
- **Modern UI**: Beautiful and responsive design powered by Tailwind CSS
- **User Management**: Registration, login, and user dashboard
- **Flash Messages**: User-friendly notifications for actions

## Project Structure

```
/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── templates/            # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── home.html         # Home page
│   ├── login.html        # Login page
│   ├── register.html     # Registration page
│   └── dashboard.html    # User dashboard
├── static/               # Static files
│   └── css/              # CSS files (Tailwind via CDN)
└── blockchain/           # Blockchain-related files (placeholder)
```

## Installation

1. **Clone or download the project**

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Open your browser** and navigate to `http://localhost:5001`

## Usage

### Home Page (`/`)
- Landing page with feature overview
- Navigation to login/register pages

### Registration (`/register`)
- Create a new user account
- Requires username, email, and password
- Validates unique username and email

### Login (`/login`)
- Sign in with username and password
- Redirects to dashboard on success

### Dashboard (`/dashboard`)
- Protected route (requires authentication)
- Displays user information and statistics
- Quick actions for navigation

### Logout (`/logout`)
- Clears session and redirects to home

## Database

The application uses SQLite with the following model:

- **User**: Stores user account information
  - `id`: Primary key
  - `username`: Unique username
  - `email`: Unique email address
  - `password_hash`: Hashed password
  - `created_at`: Account creation timestamp

## Styling

The application uses Tailwind CSS via CDN for:
- Responsive design
- Modern UI components
- Consistent color scheme
- Hover effects and transitions

## Security Features

- Password hashing using Werkzeug
- Session-based authentication
- Protected routes with login required decorator
- Flash messages for user feedback
- Form validation

## Development

To run in development mode:
```bash
export FLASK_ENV=development  # On Windows: set FLASK_ENV=development
python app.py
```

## Customization

- **Secret Key**: Change the `SECRET_KEY` in `app.py` for production
- **Database**: Modify `SQLALCHEMY_DATABASE_URI` for different databases
- **Styling**: Customize Tailwind configuration in `templates/base.html`
- **Routes**: Add new routes in `app.py`
- **Models**: Extend the database models as needed

## Production Deployment

For production deployment:
1. Change the secret key
2. Use a production WSGI server (Gunicorn, uWSGI)
3. Set up a proper database (PostgreSQL, MySQL)
4. Configure environment variables
5. Set up HTTPS

## License

This project is open source and available under the MIT License.
# Hack_squad
