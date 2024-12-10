import os
import requests
from datetime import datetime
from data_models import db, Author, Book
from flask import Flask, request, render_template, redirect, url_for, flash
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY')

# Get the absolute path to the current directory
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{base_dir}/data/library1.sqlite"

db.init_app(app)

# Create the database tables. Run once
# with app.app_context():
#    db.create_all()


def parse_date(date_str):
    """
    Handle dates and return python objects that are usable
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


def log(example):
    """
    Simple log mechanism to save every action that happens to the site in a txt file
    """
    with open('static/log.txt', 'a') as file:
        file.writelines(example + '\n')


def fetch_cover_img(isbn):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        response = requests.get(url)
        data = response.json()
        if "items" in data:
            return data['items'][0]['volumeInfo'].get(
                'imageLinks', {}).get('thumbnail', '/static/default_cover.png')
    except Exception as e:
        print(f"Error fetching cover image: {e}")
    except RequestException as h:
        print(f"Error: {h} ")

    return 'static/default_cover.png'  # Error handling of no img


@app.route("/", methods=["GET"])
def home():
    sort_by = request.args.get("sort_by", "title")  # Default to "title" if not specified
    keyword = request.args.get("keyword", "")

    # Query books and apply sorting
    query = Book.query
    if keyword:
        query = query.filter(Book.title.ilike(f"%{keyword}%"))
    if sort_by == "author":
        query = query.join(Author).order_by(Author.name)
    else:
        query = query.order_by(Book.title)

    books = query.options(db.joinedload(Book.author)).all()

    return render_template("home.html", books=books, sort_by=sort_by, keyword=keyword)


@app.route('/add_author', methods=['GET', 'POST'])
def add_author():

    if request.method == 'POST':
        name = request.form.get('name').strip()
        birth_date = request.form.get('birth_date').strip()
        death_date = request.form.get('death_date').strip()

        # if no name given error handling
        if not name:
            warning_msg = "Author name is required."
            return render_template("add_author.html", warning_msg=warning_msg)

        # creating Author obj
        author = Author(
            name=name,
            birth_date=parse_date(birth_date),
            death_date=parse_date(death_date)
        )

        try:
            db.session.add(author)
            db.session.commit()
            success_msg = "Author created successfully!"
            log_msg = f" Author '{author}' created successfully!"
            log(log_msg)
            return render_template("add_author.html", success_msg=success_msg)
        except SQLAlchemyError as h:
            db.session.rollback()
            failure_msg = f"Error creating Author : {h}"
            return render_template("add_author.html", failure_msg=failure_msg)

    if request.method == 'GET':
        return render_template("add_author.html")


@app.route('/add_book', methods=['GET', 'POST'])
def add_book():

    if request.method == 'POST':
        author_id = request.form.get('author_id')
        isbn = request.form.get('isbn').strip()
        title = request.form.get('title').strip()
        publication_year = request.form.get('publication_year').strip()
        rating = request.form.get('rating').strip()

        if not title and isbn:
            warning_msg = "Title and ISBN are required!"
            return render_template("add_book.html", authors=Author.query.all(),
                                   warning_msg=warning_msg)

        # Create Book obj
        book = Book(
            author_id=author_id,
            isbn=isbn,
            title=title,
            publication_year=publication_year if publication_year else None,
            cover_img_url=fetch_cover_img(isbn),
            rating=rating
        )
        try:
            db.session.add(book)
            db.session.commit()
            success_msg = "Book created successfully!"
            log_msg = f"Book '{book}' created successfully!!"
            log(log_msg)
            return render_template("add_book.html", authors=Author.query.all(),
                                   success_msg=success_msg)
        except SQLAlchemyError as h:
            db.session.rollback()
            failure_msg = f"Error creating Book : {h}"
            return render_template("add_book.html", authors=Author.query.all(),
                                   failure_msg=failure_msg)
    return render_template("add_book.html", authors=Author.query.all())


@app.route('/book/<int:book_id>/delete', methods=['POST'])
def delete_book(book_id):
    """
    Deletes a book by its ID.
    Also deletes the author if no other books are linked to the author.
    """
    try:
        # Find the book by ID
        del_book = db.session.query(Book).filter(Book.id == book_id).first()
        if not del_book:
            flash(f"Book with ID {book_id} not found!", "error")
            return redirect(url_for("home"))

        # Store book details for feedback
        book_title = del_book.title
        author_id = del_book.author_id
        log_msg_book = f"Book '{del_book}' has been deleted successfully!"

        # Delete the book
        db.session.delete(del_book)
        log(log_msg_book)
        flash(f"Book '{book_title}' has been deleted successfully!", "success")

        # Check if the author has other books and delete the author if no
        if not db.session.query(Book).filter(Book.author_id == author_id).count():
            del_author = db.session.query(Author).filter(Author.id == author_id).first()
            if del_author:
                db.session.delete(del_author)
                log_msg_author = f"Author without books '{del_author}' has been deleted successfully!"
                log(log_msg_author)
                flash(f"Author '{del_author}' had no books left and alt+F4'ed the database!")

        # Commit the changes
        db.session.commit()
        return redirect(url_for("home"))

    except IntegrityError as e:
        db.session.rollback()
        flash("Database integrity error occurred during deletion.", "error")
        print(f"IntegrityError: {e}")
        return redirect(url_for("home"))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash("An unexpected error occurred. Please try again.", "error")
        print(f"SQLAlchemyError: {e}")
        return redirect(url_for("home"))


@app.route('/author/<int:author_id>/delete', methods=['POST'])
def delete_author(author_id):
    try:
        author = Author.query.get_or_404(author_id)
        db.session.delete(author)
        db.session.commit()
        log_msg = f"Author '{author}' and their books were deleted successfully!"
        log(log_msg)
        flash(f"Author '{author.name}' and their books were deleted successfully!", 'success')
        return redirect(url_for('home'))

    except IntegrityError as e:
        db.session.rollback()
        flash("Database integrity error occurred during deletion.", "error")
        print(f"IntegrityError: {e}")
        return redirect(url_for("home"))

    except SQLAlchemyError as e:
        db.session.rollback()
        flash("An unexpected error occurred. Please try again.", "error")
        print(f"SQLAlchemyError: {e}")
        return redirect(url_for("home"))


@app.route('/book/<int:book_id>')
def book_details(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('book_details.html', book=book)


@app.route('/author/<int:author_id>')
def author_details(author_id):
    author = Author.query.get_or_404(author_id)
    return render_template('author_details.html', author=author)


@app.route('/book/<int:book_id>/rate', methods=['POST'])
def rate_book(book_id):
    book = Book.query.get_or_404(book_id)
    new_rating = request.form.get('rating', type=int)
    if 1 <= new_rating <= 10:
        book.rating = new_rating
        db.session.commit()
        flash(f"Updated rating for '{book.title}' to {new_rating}/10!", 'success')
    else:
        flash("Rating must be between 1 and 10.", 'error')
    return redirect(url_for('book_details', book_id=book.id))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
