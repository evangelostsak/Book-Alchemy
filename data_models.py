from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship


db = SQLAlchemy()


class Author(db.Model):
    """
    Author model
    attr:
        id (int): Primary key, auto-incremented identifier for the author.
            name (str): Name of the author.
            birth_date (str): Birth date of the author.
            death_date (str): Death date of the author (optional).
            books (relationship): Collection of books written by the author.
    """
    __table_name__ = 'authors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=True)
    death_date = Column(Date, nullable=True)

    def __repr__(self):
        """
        Returns a string representation of the Author instance for debugging.
        """
        return f"Author(id = {self.id}, name = {self.name})"

    def __str__(self):
        """
        Returns a human-readable string representation of the Author instance.
        """
        return f"{self.id}. {self.name} ({self.birth_date} - {self.date_of_death})"


class Book(db.Model):
    """
    Book model
    attr:
        id (int): Primary key, auto-incremented identifier for the book.
        author_id (int): Foreign key linking to the author of the book.
        title (str): Title of the book.
        publication_year (str): Year of publication of the book (optional).
        isbn (int): ISBN of the book.
    """
    __table_name__ = 'books'

    id = Column(Integer, primary_key=True, autoincrement=True)
    isbn = Column(Integer, nullable=False, unique=True)
    title = Column(String, nullable=False)
    publication_year = Column(Integer, nullable=True)
    author_id = Column(Integer, ForeignKey('authors.id'), nullable=False)

    author = relationship('Author', backref='books', lazy=True)

    def __repr__(self):
        """Returns a string representation of the Book model, debugging-friendly"""
        return (f"Book(id = {self.id}, isbn = {self.isbn}, title = {self.title}, "
                f"publication_year = {self.publication_year}, cover_url = {self.cover_url}, "
                f"description = {self.description})")

    def __str__(self):
        """Returns a human-readable string of the Book model"""
        return f"{self.id}. {self.title} ({self.publication_year})"
