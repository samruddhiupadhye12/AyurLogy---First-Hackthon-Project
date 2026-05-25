from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import mysql.connector
from mysql.connector import Error
import os
from dotenv import load_dotenv
from datetime import datetime

# Load .env file
load_dotenv()

app = Flask(__name__)

# Secret Key
app.secret_key = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")

# Database Configuration
DB_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'user': os.getenv("DB_USER", "root"),
    'password': os.getenv("DB_PASSWORD", ""),
    'database': os.getenv("DB_NAME", "hackathon_db")
}


def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None


@app.route('/')
def index():
    """Redirect root to feedback page"""
    return redirect(url_for('feedback'))


@app.route('/feedback')
def feedback():
    """Display the feedback form"""
    return render_template('feedback.html')


@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    """Handle feedback form submission"""
    try:
        # Get form data
        rating = request.form.get('rating', '').strip()
        message = request.form.get('message', '').strip()

        # Validation
        if not rating:
            flash('Please select a rating!', 'error')
            return redirect(url_for('feedback'))
        
        if not message:
            flash('Please write your feedback message!', 'error')
            return redirect(url_for('feedback'))

        # Validate rating is a number between 1-5
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                raise ValueError("Rating must be between 1 and 5")
        except ValueError:
            flash('Invalid rating value!', 'error')
            return redirect(url_for('feedback'))

        # Sanitize message (basic - prevent SQL injection)
        if len(message) > 5000:  # Reasonable limit
            flash('Feedback message is too long!', 'error')
            return redirect(url_for('feedback'))

        # Insert into database
        connection = get_db_connection()
        if connection is None:
            flash('Database connection error. Please try again later.', 'error')
            return redirect(url_for('feedback'))

        try:
            cursor = connection.cursor()
            sql = "INSERT INTO feedback (rating, message) VALUES (%s, %s)"
            cursor.execute(sql, (rating, message))
            connection.commit()
            cursor.close()
            flash('🌿 Thank you for your feedback!', 'success')
        except Error as e:
            print(f"Database error: {e}")
            flash('Error saving feedback. Please try again.', 'error')
        finally:
            if connection.is_connected():
                connection.close()

        return redirect(url_for('feedback'))

    except Exception as e:
        print(f"Unexpected error: {e}")
        flash('An unexpected error occurred. Please try again.', 'error')
        return redirect(url_for('feedback'))


@app.route('/api/feedback', methods=['GET'])
def get_feedback():
    """API endpoint to retrieve all feedback (optional - for admin/viewing feedback)"""
    try:
        connection = get_db_connection()
        if connection is None:
            return jsonify({'error': 'Database connection failed'}), 500

        cursor = connection.cursor(dictionary=True)
        cursor.execute("SELECT id, rating, message, created_at FROM feedback ORDER BY created_at DESC")
        feedback_list = cursor.fetchall()
        cursor.close()
        connection.close()

        return jsonify({'feedback': feedback_list}), 200
    except Error as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    # Test database connection on startup
    test_conn = get_db_connection()
    if test_conn:
        print("✓ Database connection successful!")
        test_conn.close()
    else:
        print("✗ Database connection failed! Please check your .env file and MySQL server.")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
