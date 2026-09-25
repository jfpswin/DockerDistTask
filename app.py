from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from abc import ABC, abstractmethod

PORT = int(os.environ.get("PORT", 5000))
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
USE_HTTPS = os.environ.get("USE_HTTPS", "false").lower() == "true"

app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

# 4 Classes, Book, OnlineBookStore, ItemOrder, ShoppingCart
class TangibleItem(ABC):
    def __init__(self, stock_num: int, name: str, price: float):
        self.stock_num = stock_num
        self.name = name
        self.price = price

    @abstractmethod
    def get_price(self) -> float:  # ← was empty (syntax error)
        pass

class Book(TangibleItem):
    def __init__(self, isbn: int, name: str, author: str, genre: str, edition: str, pages: int, cover: int, price: float):
        self.isbn = isbn
        self.name = name
        self.author = author
        self.genre = genre
        self.edition = edition
        self.pages = pages
        self.cover = cover 
        self.price = price

    def to_dict(self) -> dict:
        return {
            "isbn":         self.isbn,
            "name":         self.name,
            "author":       self.author,
            "genre":        self.genre,
            "edition":      self.edition,
            "pages":        self.pages,
            "cover":        self.cover,
            "price":        self.price,
        }

    def get_price(self) -> float:
        return self.price

class BookStore:
    """Manages the collection of books logic."""

    def __init__(self):
        self._books: list[Book] = []

    def add_book(self, book: Book) -> None:
        self._books.append(book)

    def get_all(self) -> list[Book]:
        return list(self._books)

    def get_by_isbn(self, isbn: int) -> Book | None:
        return next((b for b in self._books if b.isbn == isbn), None)
    
    def sort_by(self, field: str) -> list[Book]:
        key_map = {
            "author":   lambda b: b.author.lower(),
            "pages":    lambda b: b.pages,
            "genre":    lambda b: b.genre.lower(),
            "original": lambda b: b.isbn,
        }
        key = key_map.get(field, lambda b: b.isbn)
        return sorted(self._books, key=key)
 
    def search(self, query: str) -> list[Book]:
        q = query.lower()
        return [b for b in self._books
                if q in b.name.lower() or q in b.author.lower()]

class ItemOrder:
    def __init__(self, book: Book, quantity: int, price: float):
        self.book = book
        self.quantity = quantity
        self.price = price
        
    def add_item(self, book: Book) -> None:
        self.shoppingCart.append(book)

    def remove_item(self, book: Book) -> None:
        self.shoppingCart.remove(book)

class ShoppingCart:
    def __init__(self):
        self.orders: list[ItemOrder] = []

    def add_item(self, book: Book, quantity: int = 1) -> None:
        self.orders.append(ItemOrder(book, quantity, book.price))

    def remove_item(self, book: Book) -> None:
        self.orders = [o for o in self.orders if o.book.isbn != book.isbn]

#Starting data
store = BookStore()
for raw in [
    (1, "The Great Gatsby",       "F. Scott Fitzgerald", "Classic",   "First",    180, 0, 21.99),
    (2, "To Kill a Mockingbird",  "Harper Lee",          "Classic",   "First",    336, 1, 25.00),
    (3, "Fahrenheit 451",         "Ray Bradbury",        "Sci-Fi",    "Original", 256, 2, 19.99),
    (4, "Nineteen Eighty-Four",   "George Orwell",       "Dystopian", "Penguin",  328, 3, 23.99),
    (5, "Pride and Prejudice",    "Jane Austen",         "Romance",   "Oxford",   432, 4, 26.99),
    (6, "The Hobbit",             "J.R.R. Tolkien",      "Fantasy",   "Revised",  310, 5, 15.00),
]:
    store.add_book(Book(*raw))
 
#Routes
cart: dict[int, int] = {}
 
@app.route("/")
def index():
    """Serve the frontend HTML."""
    return send_from_directory(".", "index.html")
 
@app.route("/api/books", methods=["GET"])
def get_books():
    sort = request.args.get("sort", "original")
    books = store.sort_by(sort)
    return jsonify([b.to_dict() for b in books])
 
@app.route("/api/books/search", methods=["GET"])
def search_books():
    q = request.args.get("q", "")
    results = store.search(q) if q else store.get_all()
    return jsonify([b.to_dict() for b in results])
 
@app.route("/add_item", methods=["POST"])
def add_item():
    data = request.get_json(force=True)
    book_id = data.get("book_id")
    book = store.get_by_isbn(book_id)
    cart[book_id] = cart.get(book_id, 0) + 1
    if not book:
        return jsonify({"message": "Book not found"}), 404
    return jsonify({"message": f"'{book.name}' added to cart."})

@app.route("/api/cart", methods=["GET"])
def get_cart():
    items = []
    for isbn, qty in cart.items():
        book = store.get_by_isbn(isbn)
        if book:
            items.append({**book.to_dict(), "quantity": qty})
    return jsonify(items)

@app.route("/api/cart/remove", methods=["POST"])
def remove_from_cart():
    data = request.get_json(force=True)
    cart.pop(data.get("isbn"), None)
    return jsonify({"message": "Removed"})

@app.route("/api/cart/update", methods=["POST"])
def update_quantity():
    data = request.get_json(force=True)
    isbn, qty = data.get("isbn"), data.get("quantity", 1)
    if isbn in cart:
        cart.pop(isbn) if qty <= 0 else cart.update({isbn: qty})
    return jsonify({"message": "Updated"})

#Entry point
if __name__ == "__main__":
    scheme = "https" if USE_HTTPS else "http"
    print(f"Bookstore running -> {scheme}://0.0.0.0:{PORT} (debug={DEBUG})")
    if USE_HTTPS:
        app.run(host="0.0.0.0", port=PORT, debug=DEBUG, ssl_context="adhoc")
    else:
        app.run(host="0.0.0.0", port=PORT, debug=DEBUG)