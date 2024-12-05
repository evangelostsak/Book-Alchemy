from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Base Class for database models."""
    pass


db = SQLAlchemy(model_class=Base)


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
    id: db.Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    name: db.Mapped[str] = db.mapped_column(nullable=False)
    birth_date: db.Mapped[str] = db.mapped_column(nullable=False)
    death_date: db.Mapped[str] = db.mapped_column()
    books = db.relationship('Book', backref='author', lazy=True)

    def __repr__(self):
        """Returns a string representation of the Author model, debugging-friendly"""
        return f"Author(id={self.id}, name={self.name})"

    def __str__(self):
        """Returns a human-readable string of the Author model"""
        death = self.death_date if self.death_date else ""
        if death:
            return f"{self.id}. {self.name}, ({self.birth_date} - {death})"
        else:
            return f"{self.id}. {self.name}, ({self.birth_date})"


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
    id: db.Mapped[int] = db.mapped_column(primary_key=True, autoincrement=True)
    author_id: db.Mapped[int] = db.mapped_column(db.ForeignKey('author.id'))
    title: db.Mapped[str] = db.mapped_column(nullable=False)
    publication_year: db.Mapped[str] = db.mapped_column()
    isbn: db.Mapped[int] = db.mapped_column()

    def __repr__(self):
        """Returns a string representation of the Book model, debugging-friendly"""
        return f"Book(id={self.id}, title={self.title})"

    def __str__(self):
        """Returns a human-readable string of the Book model"""
        pub_year = self.publication_year if self.publication_year else ""
        if pub_year:
            return f"{self.id}. {self.title} ({pub_year})"
        else:
            return f"{self.id}. {self.title}"




