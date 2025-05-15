from flask import Flask, render_template, request, redirect, session, url_for, flash
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = '8197'

# MySQL config
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="",
    database="movie"
)
cursor = db.cursor(dictionary=True)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        cursor.execute("INSERT INTO Users (Name, Email, PasswordHash, Role) VALUES (%s, %s, %s, 'user')", (name, email, password))
        db.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        cursor.execute("SELECT * FROM Users WHERE Email=%s", (email,))
        user = cursor.fetchone()
        if user and check_password_hash(user['PasswordHash'], password):
            session['user_id'] = user['UserID']
            session['role'] = user['Role']
            return redirect('/movies')
        flash('Invalid credentials')
    return render_template('login.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username == 'airline' and password == 'rnsit':
            session['role'] = 'admin'
            return redirect('/dashboard')
        flash('Invalid Username or Password')
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('dashboard.html')
    return redirect('/login')

@app.route('/movies')
def movies():
    if 'user_id' not in session:
        return redirect('/login')

    search_term = request.args.get('search', '')
    if search_term:
        cursor.execute("SELECT * FROM Movies WHERE Title LIKE %s", ('%' + search_term + '%',))
    else:
        cursor.execute("SELECT * FROM Movies")
    movies = cursor.fetchall()
    return render_template('movies.html', movies=movies)

@app.route('/book_ticket/<int:movie_id>', methods=['GET', 'POST'])
def book_ticket(movie_id):
    if 'user_id' not in session:
        return redirect('/login')

    cursor.execute("SELECT * FROM Movies WHERE MovieID = %s", (movie_id,))
    movie = cursor.fetchone()

    if request.method == 'POST':
        showtime_id = request.form['showtime_id']
        num_tickets = int(request.form['num_tickets'])
        cursor.execute("""
            INSERT INTO Bookings (ShowtimeID, UserID, NumTickets)
            VALUES (%s, %s, %s)
        """, (showtime_id, session['user_id'], num_tickets))
        db.commit()

        cursor.execute("""
            SELECT b.BookingID, m.Title, s.ShowDate, s.ShowTime, b.NumTickets
            FROM Bookings b
            JOIN Showtimes s ON b.ShowtimeID = s.ShowtimeID
            JOIN Movies m ON s.MovieID = m.MovieID
            WHERE b.UserID = %s ORDER BY b.BookingTime DESC LIMIT 1
        """, (session['user_id'],))
        booking = cursor.fetchone()

        return render_template('booking_confirmation.html', booking=booking)

    cursor.execute("SELECT * FROM Showtimes WHERE MovieID = %s", (movie_id,))
    showtimes = cursor.fetchall()
    return render_template('book_ticket.html', movie=movie, showtimes=showtimes)
@app.route('/admin_view_bookings')
def admin_view_bookings():
    if 'role' not in session or session['role'] != 'admin':
        return redirect('/login')  # Redirect to login if not admin

    cursor.execute("""
        SELECT b.BookingID, u.Name, m.Title, s.ShowDate, s.ShowTime, b.NumTickets
        FROM Bookings b
        JOIN Users u ON b.UserID = u.UserID
        JOIN Showtimes s ON b.ShowtimeID = s.ShowtimeID
        JOIN Movies m ON s.MovieID = m.MovieID
    """)
    bookings = cursor.fetchall()

    return render_template('view_bookings.html', bookings=bookings)

@app.route('/add_movie', methods=['GET', 'POST'])
def add_movie():
    if session.get('role') != 'admin':
        return redirect('/login')
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        duration = request.form['duration']
        language = request.form['language']
        cursor.execute("INSERT INTO Movies (Title, Description, Duration, Language) VALUES (%s, %s, %s, %s)",
                       (title, description, duration, language))
        db.commit()
        return redirect('/dashboard')
    return render_template('add_movie.html')

@app.route('/add_showtime', methods=['GET', 'POST'])
def add_showtime():
    if session.get('role') != 'admin':
        return redirect('/login')
    cursor.execute("SELECT * FROM Movies")
    movies = cursor.fetchall()
    if request.method == 'POST':
        movie_id = request.form['movie_id']
        show_date = request.form['show_date']
        show_time = request.form['show_time']
        screen_number = request.form['screen_number']
        cursor.execute("INSERT INTO Showtimes (MovieID, ShowDate, ShowTime, ScreenNumber) VALUES (%s, %s, %s, %s)",
                       (movie_id, show_date, show_time, screen_number))
        db.commit()
        return redirect('/dashboard')
    return render_template('add_showtime.html', movies=movies)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
