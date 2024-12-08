import os
import requests
from datetime import datetime
from data_models import db, Author, Book
from flask import Flask, request, render_template, redirect, url_for
from requests.exceptions import RequestException
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

app = Flask(__name__)

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


def fetch_cover_img(isbn):
    try:
        url = f"https://www.googleapis.com/books/v1/volumes?q=isbn:{isbn}"
        response = requests.get(url)
        data = response.json()
        if "items" in data:
            return data['items'][0]['volumeInfo'].get('imageLinks', {}).get('thumbnail', '/static/default_cover.png')
    except Exception as e:
        print(f"Error fetching cover image: {e}")
    return '/static/default_cover.png'  # Error handling of no img


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

    books = query.all()

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
            cover_img_url=fetch_cover_img(isbn)
        )
        try:
            db.session.add(book)
            db.session.commit()
            success_msg = "Book created successfully!"
            return render_template("add_book.html", authors=Author.query.all(),
                                   success_msg=success_msg)
        except SQLAlchemyError as h:
            db.session.rollback()
            failure_msg = f"Error creating Book : {h}"
            return render_template("add_book.html", authors=Author.query.all(),
                                   failure_msg=failure_msg)
    return render_template("add_book.html", authors=Author.query.all())


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
