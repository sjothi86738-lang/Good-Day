from flask import Flask, request, jsonify, render_template_string, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import qrcode
import io
import base64
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# Database setup
def init_db():
    conn = sqlite3.connect('library.db')
    c = conn.cursor()
    
    # Create books table
    c.execute('''
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT,
            publication_year INTEGER,
            description TEXT,
            copies INTEGER DEFAULT 1,
            available INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create borrowing history table
    c.execute('''
        CREATE TABLE IF NOT EXISTS borrow_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT NOT NULL,
            borrower_name TEXT NOT NULL,
            borrower_email TEXT,
            borrow_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            return_date TIMESTAMP,
            status TEXT DEFAULT 'borrowed',
            FOREIGN KEY (isbn) REFERENCES books (isbn)
        )
    ''')
        # Insert sample data including CSE books
    sample_books = [
        # Original fiction books
        ('9780142424179', 'The Fault in Our Stars', 'John Green', 'Fiction', 2012, 
         'A touching story about two teenagers with cancer who fall in love.', 3, 2),
        ('9780545010221', 'Harry Potter and the Deathly Hallows', 'J.K. Rowling', 'Fiction', 2007,
         'The final installment in the Harry Potter series.', 5, 1),
        ('9780316769488', 'The Catcher in the Rye', 'J.D. Salinger', 'Fiction', 1951,
         'A classic coming-of-age story about Holden Caulfield.', 2, 0),

        # Already present CSE books
        ('9780262033848', 'Introduction to Algorithms', 'Thomas H. Cormen, Charles E. Leiserson', 'Computer Science', 2009,
         'Comprehensive introduction to algorithms and data structures', 5, 4),
        ('9780134494166', 'Clean Code: A Handbook of Agile Software Craftsmanship', 'Robert C. Martin', 'Programming', 2008,
         'Best practices for writing clean, maintainable code', 3, 2),
        ('9780135957059', 'The Pragmatic Programmer', 'David Thomas, Andrew Hunt', 'Programming', 2019,
         'Your journey to mastery in software development', 4, 3),
        ('9781449355739', 'Designing Data-Intensive Applications', 'Martin Kleppmann', 'Database', 2017,
         'The big ideas behind reliable, scalable, and maintainable systems', 3, 1),
        ('9780596007126', 'Head First Design Patterns', 'Eric Freeman, Elisabeth Robson', 'Software Engineering', 2004,
         'A brain-friendly guide to design patterns', 2, 2),
        ('9780134052502', 'Operating System Concepts', 'Abraham Silberschatz, Peter Baer Galvin', 'Operating Systems', 2018,
         'Comprehensive introduction to operating systems', 4, 3),
        ('9780134685991', 'Effective Java', 'Joshua Bloch', 'Programming', 2017,
         'Best practices for the Java programming language', 3, 3),
        ('9781593279509', 'Eloquent JavaScript', 'Marijn Haverbeke', 'Web Development', 2018,
         'A modern introduction to programming with JavaScript', 4, 2),
        ('9780132350884', 'Clean Architecture', 'Robert C. Martin', 'Software Architecture', 2017,
         'A craftsman\'s guide to software structure and design', 3, 1),
        ('9780596516178', 'JavaScript: The Good Parts', 'Douglas Crockford', 'Web Development', 2008,
         'Unearthing the excellence in JavaScript', 2, 0),
        ('9780262046305', 'Artificial Intelligence: A Modern Approach', 'Stuart Russell, Peter Norvig', 'Artificial Intelligence', 2020,
         'Comprehensive introduction to artificial intelligence', 5, 3),

        # ✅ Additional 20 CSE Books
        ('9780131103627', 'The C Programming Language', 'Brian W. Kernighan, Dennis M. Ritchie', 'Programming', 1988,
         'Classic reference for C programming by the creators of the language', 4, 3),
        ('9780201633610', 'Design Patterns: Elements of Reusable Object-Oriented Software', 'Erich Gamma, Richard Helm, Ralph Johnson, John Vlissides', 'Software Engineering', 1994,
         'The Gang of Four book on design patterns', 3, 2),
        ('9780262035613', 'Deep Learning', 'Ian Goodfellow, Yoshua Bengio, Aaron Courville', 'Artificial Intelligence', 2016,
         'Foundational textbook on deep learning and neural networks', 5, 4),
        ('9780262510875', 'Structure and Interpretation of Computer Programs', 'Harold Abelson, Gerald Jay Sussman', 'Programming Languages', 1996,
         'A legendary introduction to computer science concepts', 3, 2),
        ('9780131101630', 'Computer Networks', 'Andrew S. Tanenbaum, David J. Wetherall', 'Networking', 2011,
         'Comprehensive textbook on computer networks', 5, 4),
        ('9780132143011', 'Database System Concepts', 'Abraham Silberschatz, Henry Korth, S. Sudarshan', 'Database', 2010,
         'Comprehensive introduction to database systems', 4, 3),
        ('9780123748560', 'Computer Organization and Design', 'David A. Patterson, John L. Hennessy', 'Computer Architecture', 2014,
         'Textbook on computer organization and design principles', 5, 4),
        ('9781558606043', 'Modern Operating Systems', 'Andrew S. Tanenbaum', 'Operating Systems', 2001,
         'Classic OS textbook by Tanenbaum', 4, 3),
        ('9780596009205', 'Learning Python', 'Mark Lutz', 'Programming', 2013,
         'Comprehensive guide to Python programming', 5, 4),
        ('9781449331818', 'Fluent Python', 'Luciano Ramalho', 'Programming', 2015,
         'Best practices for writing Pythonic code', 3, 2),
        ('9781491903995', 'Python for Data Analysis', 'Wes McKinney', 'Data Science', 2017,
         'Practical guide for analyzing data with Python and Pandas', 4, 3),
        ('9781788622212', 'Mastering React', 'Adam Horton, Ryan Vice', 'Web Development', 2018,
         'Advanced guide for mastering React.js', 3, 2),
        ('9781492051367', 'Learning React', 'Alex Banks, Eve Porcello', 'Web Development', 2020,
         'Beginner-friendly guide to learning React.js', 4, 3),
        ('9781492052203', 'Kubernetes: Up and Running', 'Kelsey Hightower, Brendan Burns, Joe Beda', 'Cloud Computing', 2019,
         'Guide to deploying and managing applications with Kubernetes', 3, 2),
        ('9781491950357', 'Site Reliability Engineering', 'Niall Richard Murphy, Betsy Beyer', 'DevOps', 2016,
         'Google’s guide to building reliable, scalable systems', 2, 1),
        ('9781118026472', 'Cybersecurity and Cyberwar: What Everyone Needs to Know', 'P.W. Singer, Allan Friedman', 'Cybersecurity', 2014,
         'Essential introduction to cybersecurity concepts', 3, 2),
        ('9783319924263', 'Computer Vision: Algorithms and Applications', 'Richard Szeliski', 'Artificial Intelligence', 2022,
         'Comprehensive book on modern computer vision techniques', 4, 3),
        ('9781119706670', 'Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow', 'Aurélien Géron', 'Machine Learning', 2019,
         'Practical guide for machine learning and deep learning', 5, 4),
        ('9780262039246', 'Algorithms to Live By', 'Brian Christian, Tom Griffiths', 'Computer Science', 2016,
         'How computer science algorithms apply to everyday life', 3, 2),
        ('9780133594140', 'Computer Security: Principles and Practice', 'William Stallings, Lawrie Brown', 'Cybersecurity', 2017,
         'Comprehensive introduction to computer security concepts', 4, 3)
    ]

    
    for book in sample_books:
        c.execute('''
            INSERT OR IGNORE INTO books 
            (isbn, title, author, category, publication_year, description, copies, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', book)
    
    conn.commit()
    conn.close()

# Database helper functions
def get_db_connection():
    conn = sqlite3.connect('library.db')
    conn.row_factory = sqlite3.Row
    return conn

def book_to_dict(book_row):
    return {
        'id': book_row['id'],
        'isbn': book_row['isbn'],
        'title': book_row['title'],
        'author': book_row['author'],
        'category': book_row['category'],
        'publication_year': book_row['publication_year'],
        'description': book_row['description'],
        'copies': book_row['copies'],
        'available': book_row['available'],
        'created_at': book_row['created_at']
    }

# QR Code generation
def generate_qr_code(isbn):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(isbn)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 string
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"

# API Routes

@app.route('/')
def home():
    return jsonify({
        "message": "Library Management System API",
        "endpoints": {
            "GET /api/books": "Get all books",
            "GET /api/books/<isbn>": "Get specific book by ISBN",
            "POST /api/books": "Add new book",
            "PUT /api/books/<isbn>": "Update book",
            "DELETE /api/books/<isbn>": "Delete book",
            "GET /api/books/<isbn>/qr": "Get QR code for book",
            "POST /api/books/<isbn>/borrow": "Borrow book",
            "POST /api/books/<isbn>/return": "Return book",
            "GET /api/search": "Search books"
        }
    })

@app.route('/api/books', methods=['GET'])
def get_all_books():
    try:
        conn = get_db_connection()
        books = conn.execute('SELECT * FROM books ORDER BY title').fetchall()
        conn.close()
        
        return jsonify([book_to_dict(book) for book in books])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<isbn>', methods=['GET'])
def get_book(isbn):
    try:
        conn = get_db_connection()
        book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
        conn.close()
        
        if book:
            return jsonify(book_to_dict(book))
        else:
            return jsonify({'error': 'Book not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books', methods=['POST'])
def add_book():
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['isbn', 'title', 'author']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'{field} is required'}), 400
        
        # Validate ISBN format (13 digits)
        isbn = data['isbn'].replace('-', '').replace(' ', '')
        if not isbn.isdigit() or len(isbn) != 13:
            return jsonify({'error': 'ISBN must be 13 digits'}), 400
        
        conn = get_db_connection()
        
        # Check if book already exists
        existing = conn.execute('SELECT id FROM books WHERE isbn = ?', (isbn,)).fetchone()
        if existing:
            conn.close()
            return jsonify({'error': 'Book with this ISBN already exists'}), 400
        
        # Insert new book
        copies = int(data.get('copies', 1))
        conn.execute('''
            INSERT INTO books (isbn, title, author, category, publication_year, 
                             description, copies, available)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            isbn,
            data['title'],
            data['author'],
            data.get('category'),
            data.get('publication_year'),
            data.get('description'),
            copies,
            copies
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Book added successfully', 'isbn': isbn}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<isbn>', methods=['PUT'])
def update_book(isbn):
    try:
        data = request.get_json()
        
        conn = get_db_connection()
        
        # Check if book exists
        book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
        if not book:
            conn.close()
            return jsonify({'error': 'Book not found'}), 404
        
        # Update book
        conn.execute('''
            UPDATE books 
            SET title = ?, author = ?, category = ?, publication_year = ?, 
                description = ?, copies = ?, available = ?
            WHERE isbn = ?
        ''', (
            data.get('title', book['title']),
            data.get('author', book['author']),
            data.get('category', book['category']),
            data.get('publication_year', book['publication_year']),
            data.get('description', book['description']),
            data.get('copies', book['copies']),
            data.get('available', book['available']),
            isbn
        ))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Book updated successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<isbn>', methods=['DELETE'])
def delete_book(isbn):
    try:
        conn = get_db_connection()
        
        # Check if book exists
        book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
        if not book:
            conn.close()
            return jsonify({'error': 'Book not found'}), 404
        
        # Delete book
        conn.execute('DELETE FROM books WHERE isbn = ?', (isbn,))
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Book deleted successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<isbn>/qr', methods=['GET'])
def get_book_qr(isbn):
    try:
        conn = get_db_connection()
        book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
        conn.close()
        
        if not book:
            return jsonify({'error': 'Book not found'}), 404
        
        qr_code = generate_qr_code(isbn)
        
        return jsonify({
            'isbn': isbn,
            'title': book['title'],
            'qr_code': qr_code
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<isbn>/borrow', methods=['POST'])
def borrow_book(isbn):
    try:
        data = request.get_json()
        borrower_name = data.get('borrower_name')
        borrower_email = data.get('borrower_email', '')
        
        if not borrower_name:
            return jsonify({'error': 'Borrower name is required'}), 400
        
        conn = get_db_connection()
        
        # Check if book exists and is available
        book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
        if not book:
            conn.close()
            return jsonify({'error': 'Book not found'}), 404
        
        if book['available'] <= 0:
            conn.close()
            return jsonify({'error': 'Book not available for borrowing'}), 400
        
        # Record borrowing
        conn.execute('''
            INSERT INTO borrow_history (isbn, borrower_name, borrower_email, status)
            VALUES (?, ?, ?, 'borrowed')
        ''', (isbn, borrower_name, borrower_email))
        
        # Update available count
        conn.execute('''
            UPDATE books SET available = available - 1 WHERE isbn = ?
        ''', (isbn,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Book borrowed successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/books/<isbn>/return', methods=['POST'])
def return_book(isbn):
    try:
        data = request.get_json()
        borrower_name = data.get('borrower_name')
        
        if not borrower_name:
            return jsonify({'error': 'Borrower name is required'}), 400
        
        conn = get_db_connection()
        
        # Check if book exists
        book = conn.execute('SELECT * FROM books WHERE isbn = ?', (isbn,)).fetchone()
        if not book:
            conn.close()
            return jsonify({'error': 'Book not found'}), 404
        
        # Find active borrow record
        borrow_record = conn.execute('''
            SELECT * FROM borrow_history 
            WHERE isbn = ? AND borrower_name = ? AND status = 'borrowed'
            ORDER BY borrow_date DESC LIMIT 1
        ''', (isbn, borrower_name)).fetchone()
        
        if not borrow_record:
            conn.close()
            return jsonify({'error': 'No active borrow record found'}), 404
        
        # Update borrow record
        conn.execute('''
            UPDATE borrow_history 
            SET return_date = CURRENT_TIMESTAMP, status = 'returned'
            WHERE id = ?
        ''', (borrow_record['id'],))
        
        # Update available count
        conn.execute('''
            UPDATE books SET available = available + 1 WHERE isbn = ?
        ''', (isbn,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'message': 'Book returned successfully'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search', methods=['GET'])
def search_books():
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
        
        conn = get_db_connection()
        
        # Search in title, author, isbn, and category
        search_pattern = f'%{query}%'
        books = conn.execute('''
            SELECT * FROM books 
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ? OR category LIKE ?
            ORDER BY title
        ''', (search_pattern, search_pattern, search_pattern, search_pattern)).fetchall()
        
        conn.close()
        
        return jsonify([book_to_dict(book) for book in books])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/borrow-history', methods=['GET'])
def get_borrow_history():
    try:
        conn = get_db_connection()
        
        history = conn.execute('''
            SELECT bh.*, b.title, b.author 
            FROM borrow_history bh
            JOIN books b ON bh.isbn = b.isbn
            ORDER BY bh.borrow_date DESC
        ''').fetchall()
        
        conn.close()
        
        return jsonify([dict(record) for record in history])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/frontend')
def serve_frontend():
    """Serve the HTML frontend"""
    try:
        # Try to find the HTML file in current directory
        if os.path.exists('index.html'):
            return send_from_directory('.', 'index.html')
        else:
            # If index.html doesn't exist, return a simple message with instructions
            return f'''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Library Management System</title>
                <style>
                    body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
                    .error {{ background: #f8d7da; border: 1px solid #f5c6cb; padding: 15px; border-radius: 5px; }}
                    .info {{ background: #d1ecf1; border: 1px solid #bee5eb; padding: 15px; border-radius: 5px; }}
                    pre {{ background: #f8f9fa; padding: 10px; border-radius: 5px; overflow-x: auto; }}
                </style>
            </head>
            <body>
                <h1>📚 Library Management System</h1>
                
                <div class="error">
                    <h3>❌ HTML Frontend Not Found</h3>
                    <p>The <code>index.html</code> file is not in the same directory as your Flask app.</p>
                </div>
                
                <div class="info">
                    <h3>🔧 How to Fix This:</h3>
                    
                    <h4>Option 1: Save the HTML file (Recommended)</h4>
                    <ol>
                        <li>Copy the HTML code from Claude's artifact</li>
                        <li>Save it as <code>index.html</code> in the same folder as your <code>app.py</code></li>
                        <li>Refresh this page</li>
                    </ol>
                    
                    <h4>Option 2: Use a separate server</h4>
                    <ol>
                        <li>Open a new terminal in your HTML file location</li>
                        <li>Run: <pre>python3 -m http.server 8080</pre></li>
                        <li>Access: <a href="http://localhost:8080/index.html">http://localhost:8080/index.html</a></li>
                    </ol>
                    
                    <h4>Option 3: Use the API directly</h4>
                    <p>Test the API endpoints:</p>
                    <ul>
                        <li><a href="/api/books">View all books</a></li>
                        <li><a href="/api/stats">View library statistics</a></li>
                        <li><a href="/generate-frontend-qr">Generate QR code</a></li>
                    </ul>
                </div>
                
                <div class="info">
                    <h3>📱 API Endpoints Available:</h3>
                    <ul>
                        <li><strong>GET /api/books</strong> - Get all books</li>
                        <li><strong>GET /api/books/&lt;isbn&gt;</strong> - Get specific book</li>
                        <li><strong>POST /api/books</strong> - Add new book</li>
                        <li><strong>GET /api/search?q=&lt;query&gt;</strong> - Search books</li>
                        <li><strong>GET /generate-frontend-qr</strong> - Generate QR for frontend</li>
                    </ul>
                </div>
            </body>
            </html>
            '''
    except Exception as e:
        return jsonify({'error': f'Error serving frontend: {str(e)}'}), 500

@app.route('/generate-frontend-qr')
def generate_frontend_qr_endpoint():
    """Generate QR code for the frontend URL"""
    try:
        frontend_url = request.url_root + 'frontend'  # e.g., http://localhost:5000/frontend
        qr_code = generate_qr_code(frontend_url)
        
        return jsonify({
            'url': frontend_url,
            'qr_code': qr_code,
            'message': 'QR code for frontend access'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_library_stats():
    try:
        conn = get_db_connection()
        
        # Get total books
        total_books = conn.execute('SELECT COUNT(*) as count FROM books').fetchone()['count']
        
        # Get total copies
        total_copies = conn.execute('SELECT SUM(copies) as total FROM books').fetchone()['total'] or 0
        
        # Get available copies
        available_copies = conn.execute('SELECT SUM(available) as total FROM books').fetchone()['total'] or 0
        
        # Get borrowed books
        borrowed_books = total_copies - available_copies
        
        # Get categories
        categories = conn.execute('''
            SELECT category, COUNT(*) as count 
            FROM books 
            WHERE category IS NOT NULL 
            GROUP BY category
            ORDER BY count DESC
        ''').fetchall()
        
        # Get recent borrowing activity
        recent_activity = conn.execute('''
            SELECT bh.*, b.title, b.author 
            FROM borrow_history bh
            JOIN books b ON bh.isbn = b.isbn
            ORDER BY bh.borrow_date DESC
            LIMIT 10
        ''').fetchall()
        
        conn.close()
        
        return jsonify({
            'total_books': total_books,
            'total_copies': total_copies,
            'available_copies': available_copies,
            'borrowed_books': borrowed_books,
            'categories': [dict(cat) for cat in categories],
            'recent_activity': [dict(activity) for activity in recent_activity]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    # Run the app
    app.run(debug=True, host='0.0.0.0', port=6969)