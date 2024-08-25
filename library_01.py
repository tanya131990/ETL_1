import pymongo
import datetime
import random
from collections import defaultdict
import matplotlib.pyplot as plt

# Настройки подключения к MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["library"]

# Коллекции
users_collection = db["users"]
books_collection = db["books"]
borrow_history_collection = db["borrow_history"]

# --- Модели ---

class Book:
    def __init__(self, title, author, genre, isbn, year, rating=0.0, available=True):
        self.title = title
        self.author = author
        self.genre = genre
        self.isbn = isbn
        self.year = year
        self.rating = rating
        self.available = available

    def __repr__(self):
        return f"Книга: '{self.title}' ({self.author}), жанр: {self.genre}, ISBN: {self.isbn}, " \
               f"год: {self.year}, рейтинг: {self.rating}, доступна: {self.available}"

    def to_dict(self):
        """Преобразует объект Book в словарь."""
        return {
            "title": self.title,
            "author": self.author,
            "genre": self.genre,
            "isbn": self.isbn,
            "year": self.year,
            "rating": self.rating,
            "available": self.available
        }


class User:
    def __init__(self, name, email, password, role="user", _id=None):  # Добавлен _id
        self.name = name
        self.email = email
        self.password = password
        self.role = role
        self._id = _id  # Сохранение id пользователя

    def __repr__(self):
        return f"Пользователь: '{self.name}', email: {self.email}, роль: {self.role}"

    def to_dict(self):
        """Преобразует объект User в словарь."""
        return {
            "name": self.name,
            "email": self.email,
            "password": self.password,
            "role": self.role
        }

# --- ETL-функции ---

def generate_random_books(count=10):
    """Генерирует тестовые данные о книгах."""
    genres = ["Фантастика", "Детектив", "Роман", "История", "Научная фантастика"]
    authors = ["Толстой", "Достоевский", "Агата Кристи", "Джордж Оруэлл", "Артур Конан Дойл"]

    for _ in range(count):
        title = f"Книга {random.randint(1, 100)}"
        author = random.choice(authors)
        genres = random.choice(genres)
        isbn = f"ISBN-{random.randint(1000000000, 9999999999)}"
        year = random.randint(1900, 2023)
        rating = random.uniform(0.0, 5.0)
        book = Book(title, author, genres, isbn, year, rating)

        # Загрузка в MongoDB
        books_collection.insert_one(book.to_dict())
def generate_random_users(count=5):
    """Генерирует тестовые данные о пользователях."""
    names = ["Иван", "Мария", "Алексей", "Ольга", "Дмитрий"]
    emails = ["ivan@example.com", "maria@example.com", "alex@example.com", "olga@example.com", "dmitry@example.com"]

    for _ in range(count):
        name = random.choice(names)
        email = random.choice(emails)
        password = "password"  # В реальной системе пароли должны быть хэшированы
        user = User(name, email, password)

        # Загрузка в MongoDB
        users_collection.insert_one(user.to_dict())

def add_book():
    """Добавляет новую книгу (доступно только для администратора)."""
    if current_user.role == "admin":
        title = input("Введите название книги: ")
        author = input("Введите автора книги: ")
        genre = input("Введите жанр книги: ")
        isbn = input("Введите ISBN книги: ")
        year = int(input("Введите год издания: "))
        book = Book(title, author, genre, isbn, year)
        books_collection.insert_one(book.to_dict())
        print("Книга добавлена.")
    else:
        print("Доступ запрещен. Необходимо быть администратором.")

def delete_book():
    """Удаляет книгу (доступно только для администратора)."""
    if current_user.role == "admin":
        isbn = input("Введите ISBN книги для удаления: ")
        books_collection.delete_one({"isbn": isbn})
        print("Книга удалена.")
    else:
        print("Доступ запрещен. Необходимо быть администратором.")

def add_user():
    """Добавляет нового пользователя (доступно только для администратора)."""
    if current_user.role == "admin":
        name = input("Введите имя пользователя: ")
        email = input("Введите email пользователя: ")
        password = input("Введите пароль: ")
        user = User(name, email, password)
        users_collection.insert_one(user.to_dict())
        print("Пользователь добавлен.")
    else:
        print("Доступ запрещен. Необходимо быть администратором.")

def delete_user():
    """Удаляет пользователя (доступно только для администратора)."""
    if current_user.role == "admin":
        email = input("Введите email пользователя для удаления: ")
        users_collection.delete_one({"email": email})
        print("Пользователь удален.")
    else:
        print("Доступ запрещен. Необходимо быть администратором.")

def borrow_book():
    """Бронирует книгу."""
    isbn = input("Введите ISBN книги: ")
    book = books_collection.find_one({"isbn": isbn})

    if book:
        if book['available']:
            borrow_date = datetime.datetime.now()
            return_date = borrow_date + datetime.timedelta(days=14)  # 14 дней на возврат

            borrow_history_collection.insert_one({
                "user_id": current_user._id,
                "book_id": book["_id"],
                "borrow_date": borrow_date,
                "return_date": return_date
            })

            book['available'] = False
            books_collection.update_one({"isbn": isbn}, {"$set": book})

            print(f"Книга '{book['title']}' успешно взята в аренду. "
                    f"Возврат до: {return_date.strftime('%Y-%m-%d')}")
        else:
            print("Книга недоступна. Попробуйте позже.")
    else:
        print("Книга не найдена.")

def return_book():
    """Возвращает книгу."""
    isbn = input("Введите ISBN книги: ")
    book = books_collection.find_one({"isbn": isbn})

    if book:
        if not book['available']:
            borrow_history_collection.update_one(
                {"user_id": current_user._id, "book_id": book["_id"], "return_date": {"$ne": None}},
                {"$set": {"return_date": datetime.datetime.now()}}
            )

            book['available'] = True
            books_collection.update_one({"isbn": isbn}, {"$set": book})  # Отступ исправлен

            print(f"Книга '{book['title']}' успешно возвращена в библиотеку.")
        else:
            print("Книга уже была возвращена.")
    else:
        print("Книга не найдена.")


def search_book():
    """Поиск книги по названию, автору или жанру."""
    search_term = input("Введите поисковый запрос (название, автор, жанр): ")

    # Выполняем поиск
    query = {
        "$or": [
            {"title": {"$regex": search_term, "$options": "i"}},
            {"author": {"$regex": search_term, "$options": "i"}},
            {"genre": {"$regex": search_term, "$options": "i"}}
        ]
    }

    # Получаем количество документов
    count = books_collection.count_documents(query)

    if count > 0:
        print("Найденные книги:")
        for book in books_collection.find(query):
            print(f"  {book['title']} ({book['author']}), жанр: {book['genre']}, ISBN: {book['isbn']}")
    else:
        print("Книги по данному запросу не найдены.")

def get_user_borrow_history():
    """Получает историю взятия книг пользователем."""
    borrow_history = borrow_history_collection.aggregate([
        {
        "$match": {"user_id": current_user._id}
        },
        {
            "$lookup": {
                "from": "books",
                "localField": "book_id",
                "foreignField": "_id",
                "as": "book"
            }
        },
        {
            "$unwind": "$book"
        },
        {
            "$project": {
                "_id": 0,
                "book_title": "$book.title",
                "borrow_date": "$borrow_date",
                "return_date": "$return_date"
            }
        }
    ])
    print(f"История взятия книг для пользователя '{current_user.name}'")
    for entry in borrow_history:
        print(f"  Книга: '{entry['book_title']}', дата взятия: {entry['borrow_date']}, "
              f"дата возврата: {entry['return_date']}")

def get_most_popular_books(limit=5):
    """Получает список самых популярных книг (по количеству взятий)."""
    popular_books = borrow_history_collection.aggregate([
        {
            "$group": {
                "_id": "$book_id",
                "borrow_count": {"$sum": 1}
            }
        },
        {
            "$lookup": {
                "from": "books",
                "localField": "_id",
                "foreignField": "_id",
                "as": "book"
            }
        },
        {
            "$unwind": "$book"
        },
        {
            "$sort": {"borrow_count": pymongo.DESCENDING}
        },
        {
            "$limit": limit
        },
        {
            "$project": {
                "_id": 0,
                "book_title": "$book.title",
                "borrow_count": 1
            }
        }
    ])
    print("Самые популярные книги:")
    for entry in popular_books:
        print(f"  '{entry['book_title']}' - количество взятий: {entry['borrow_count']}")

def get_genre_popularity():
    """Построить диаграмму по популярности жанров."""
    genre_counts = defaultdict(int)
    for entry in borrow_history_collection.find():
        book = books_collection.find_one({"_id": entry["book_id"]})
        if book:
            genre_counts[book["genre"]] += 1

    genres = list(genre_counts.keys())
    counts = list(genre_counts.values())

    plt.figure(figsize=(10, 5))
    plt.bar(genres, counts)
    plt.xlabel("Жанр")
    plt.ylabel("Количество взятий")
    plt.title("Популярность жанров книг")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.show()

def get_overdue_books():
    """Получает список книг, которые не были возвращены в срок (доступно только для администратора)."""
    if current_user.role == "admin":
        overdue_books = borrow_history_collection.aggregate([
            {
                "$match": {"return_date": {"$lt": datetime.datetime.now()}}
            },
            {
                "$lookup": {
                    "from": "books",
                    "localField": "book_id",
                    "foreignField": "_id",
                    "as": "book"
                }
            },
            {
                "$unwind": "$book"
            },
            {
                "$lookup": {
                    "from": "users",
                    "localField": "user_id",
                    "foreignField": "_id",
                    "as": "user"
                }
            },
            {
                "$unwind": "$user"
            },
            {
                "$project": {
                    "_id": 0,
                    "book_title": "$book.title",
                    "user_name": "$user.name",
                    "borrow_date": "$borrow_date",
                    "return_date": "$return_date"
                }
            }
        ])
        print("Книги, не возвращенные в срок:")
        for entry in overdue_books:
            print(f"  '{entry['book_title']}' - пользователь: '{entry['user_name']}', дата взятия: {entry['borrow_date']}, "
                  f"дата возврата: {entry['return_date']}")
    else:
        print("Доступ запрещен. Необходимо быть администратором.")

def register_user():
    """Регистрация нового пользователя."""
    name = input("Введите имя: ")
    email = input("Введите email: ")
    password = input("Введите пароль: ")
    role = input("Введите роль (user/admin): ")  # Добавлен ввод роли

    if users_collection.find_one({"email": email}):
        print("Пользователь с таким email уже существует.")
    else:
        user = User(name, email, password, role)
        users_collection.insert_one(user.to_dict())
        print(f"Пользователь '{name}' успешно зарегистрирован!")


def login_user():
    global current_user
    email = input("Введите email: ")
    password = input("Введите пароль: ")

    user = users_collection.find_one({"email": email})
    if user and user["password"] == password:
        current_user = User(user["name"], user["email"], user["password"], user.get("role", "user"), user["_id"])  # Передаем _id
        print(f"Добро пожаловать, {current_user.name}!")
    else:
        print("Неверный email или пароль.")

# --- Основной цикл ---
current_user = None

while True:
    if current_user:
        print("\nМеню:")
        print("1. Взять книгу в аренду")
        print("2. Вернуть книгу")
        print("3. Посмотреть историю взятия книг")
        print("4. Поиск книги")
        print("5. Посмотреть самые популярные книги")
        print("6. Построить диаграмму популярности жанров")
        print("7. Выход")

        if current_user.role == "admin":
            print("8. Добавить книгу")
            print("9. Удалить книгу")
            print("10. Добавить пользователя")
            print("11. Удалить пользователя")
            print("12. Посмотреть просроченные книги")

        choice = input("Выберите действие: ")

        if choice == '1':
            borrow_book()
        elif choice == '2':
            return_book()
        elif choice == '3':
            get_user_borrow_history()
        elif choice == '4':
            search_book()
        elif choice == '5':
            get_most_popular_books()
        elif choice == '6':
            get_genre_popularity()
        elif choice == '7':
            print("До свидания!")
            break
        elif current_user.role == "admin":
            if choice == '8':
                add_book()
            elif choice == '9':
                delete_book()
            elif choice == '10':
                add_user()
            elif choice == '11':
                delete_user()
            elif choice == '12':
                get_overdue_books()
            else:
                print("Неверный выбор.")
        else:
            print("Неверный выбор.")
    else:
        print("\nМеню:")
        print("1. Зарегистрироваться")
        print("2. Войти")
        print("3. Выход")
        print("4. Загрузить тестовые данные о книгах")
        print("5. Загрузить тестовые данные о пользователях")

        choice = input("Выберите действие: ")

        if choice == '1':
            register_user()
        elif choice == '2':
            login_user()
        elif choice == '3':
            print("До свидания!")
            break
        elif choice == '4':
            generate_random_books()
            print("Тестовые данные о книгах загружены.")
        elif choice == '5':
            generate_random_users()
            print("Тестовые данные о пользователях загружены.")
        else:
            print("Неверный выбор.")