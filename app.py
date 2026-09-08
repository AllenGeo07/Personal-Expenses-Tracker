import sqlite3
from flask import Flask, render_template, request, redirect, url_for, jsonify

# Initialize the Flask application
app = Flask(__name__)

# Database configuration
DATABASE = 'expenses.db'


def get_db_connection():
    """
    Creates and returns a connection to the SQLite database.
    Using sqlite3.Row enables column access by name (e.g., row['amount']).
    """
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Initializes the database and creates the 'expenses' table if it does not already exist.
    Stores 'amount' (REAL) and 'category' (TEXT).
    """
    conn = get_db_connection()
    with conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                amount REAL NOT NULL,
                category TEXT NOT NULL
            )
        ''')
    conn.close()


def compute_total():
    """
    Helper function to calculate the sum of all expenses in the database.
    Returns 0.0 if no expenses exist.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT SUM(amount) FROM expenses')
    result = cursor.fetchone()[0]
    conn.close()
    return round(result, 2) if result is not None else 0.0


# ---------------------------------------------------------
# ROUTES
# ---------------------------------------------------------

@app.route('/', methods=['GET'])
def index():
    """
    Route to render the main page.
    Retrieves all recorded expenses and calculates the current total.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, amount, category FROM expenses ORDER BY id DESC')
    expenses = cursor.fetchall()
    conn.close()

    total = compute_total()
    return render_template('index.html', expenses=expenses, total=total)


@app.route('/add', methods=['POST'])
def add_expense():
    """
    Route to add a new expense.
    Accepts data from an HTML form (or JSON payload).
    Validates amount and category before inserting into the database.
    """
    # Check if request is JSON or standard Form data
    if request.is_json:
        data = request.get_json()
        amount = data.get('amount')
        category = data.get('category')
    else:
        amount = request.form.get('amount')
        category = request.form.get('category')

    # Basic validation
    if not amount or not category:
        if request.is_json:
            return jsonify({'error': 'Both amount and category are required'}), 400
        return redirect(url_for('index'))

    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError('Amount must be positive')
    except ValueError:
        if request.is_json:
            return jsonify({'error': 'Amount must be a valid positive number'}), 400
        return redirect(url_for('index'))

    # Clean category string
    category = category.strip()

    # Insert into database
    conn = get_db_connection()
    with conn:
        conn.execute(
            'INSERT INTO expenses (amount, category) VALUES (?, ?)',
            (amount, category)
        )
    conn.close()

    if request.is_json:
        return jsonify({'message': 'Expense added successfully', 'amount': amount, 'category': category}), 201

    # Redirect back to the main page to show the updated list and total
    return redirect(url_for('index'))


@app.route('/total', methods=['GET'])
def get_total():
    """
    Route to calculate and return the total sum of all expenses.
    Can be consumed as a JSON endpoint or viewed directly in the browser.
    """
    total = compute_total()
    return jsonify({
        'status': 'success',
        'total': total
    })


@app.route('/delete/<int:expense_id>', methods=['POST'])
def delete_expense(expense_id):
    """
    Optional helper route to delete an expense by its ID.
    """
    conn = get_db_connection()
    with conn:
        conn.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.close()
    return redirect(url_for('index'))


# ---------------------------------------------------------
# APPLICATION ENTRYPOINT
# ---------------------------------------------------------
if __name__ == '__main__':
    # Initialize the database table before the server starts
    init_db()
    # Run the Flask development server
    print("Starting Flask Expense Tracker on http://127.0.0.1:5000")
    app.run(debug=True)
