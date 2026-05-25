# 🌿 Ayurlogy Feedback Form

A complete feedback form application built with Flask and MySQL, featuring a beautiful star rating system and user-friendly interface.

## Features

- ⭐ Interactive 5-star rating system
- 📝 Feedback message submission
- 💾 MySQL database storage
- ✨ Flash messages for user feedback
- 🔒 Input validation and sanitization
- 📊 Character counter for feedback messages
- 🎨 Beautiful, responsive UI

## Prerequisites

- Python 3.7 or higher
- MySQL Server installed and running
- pip (Python package manager)

## Installation & Setup

### 1. Clone or Download the Project

Navigate to the project directory:
```bash
cd feedback
```

### 2. Create Virtual Environment (Recommended)

```bash
python -m venv venv
```

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup MySQL Database

1. Open MySQL command line or MySQL Workbench
2. Run the SQL script to create the database and table:
```bash
mysql -u root -p < feedbackDatabase.sql
```

Or manually execute the SQL commands in `feedbackDatabase.sql`:
```sql
CREATE DATABASE ayurlogy_db;
USE ayurlogy_db;
CREATE TABLE feedback (
    id INT AUTO_INCREMENT PRIMARY KEY,
    rating INT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 5. Configure Environment Variables

The `.env` file is already created with default values. Update it if needed:

```env
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=ayurlogy_db
SECRET_KEY=your_secret_key_here
```

**Important:** Change the `SECRET_KEY` to a random string for production use.

### 6. Run the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### 7. Access the Feedback Form

Open your browser and navigate to:
- **Feedback Form:** http://localhost:5000/feedback
- **Root URL:** http://localhost:5000 (redirects to feedback form)

## API Endpoints

### GET `/feedback`
Displays the feedback form page.

### POST `/submit_feedback`
Submits feedback data to the database.
- **Parameters:**
  - `rating` (required): Integer between 1-5
  - `message` (required): Text feedback message (max 5000 characters)

### GET `/api/feedback`
Retrieves all feedback entries as JSON (for viewing/admin purposes).

## Project Structure

```
feedback/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── feedbackDatabase.sql   # Database schema
├── .env                   # Environment variables
├── templates/
│   └── feedback.html      # Feedback form template
└── static/
    └── feedback.css       # Stylesheet
```

## Troubleshooting

### Database Connection Error
- Ensure MySQL server is running
- Verify credentials in `.env` file
- Check if database `ayurlogy_db` exists
- Make sure MySQL user has proper permissions

### Port Already in Use
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Change port number
```

### Module Not Found Error
Make sure all dependencies are installed:
```bash
pip install -r requirements.txt
```

## Security Notes

- Change the `SECRET_KEY` in `.env` for production
- Use environment variables for sensitive data
- Consider adding CSRF protection for production
- Implement rate limiting for API endpoints
- Sanitize and validate all user inputs (already implemented)

## License

This project is open source and available for use.

## Support

For issues or questions, please check:
1. Database connection settings
2. MySQL server status
3. Python version compatibility
4. All dependencies are installed correctly
