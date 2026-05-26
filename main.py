from typing import List, Tuple, Dict, Optional
from datetime import datetime, timedelta
from collections import UserDict
import pickle

class EntityAlreadyExists(ValueError):
    pass


class Field:
    """
    Базовий клас для полів запису.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    """
    Клас для зберігання імені контакту.
    Ім'я не може бути порожнім.
    """

    def __init__(self, value: str):
        value = value.strip()

        if not value:
            raise ValueError("Name cannot be empty.")

        super().__init__(value)


class Phone(Field):
    """
    Клас для зберігання номера телефону.
    Номер телефону повинен містити 10 цифр.
    """

    def __init__(self, value: str):
        if not value.isdigit() or len(value) != 10:
            raise ValueError("Phone number must contain 10 digits.")

        super().__init__(value)


class Birthday(Field):
    """
    Дата народження у форматі DD.MM.YYYY
    """

    def __init__(self, value: str):
        try:
            date = datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        super().__init__(date)


class Record:
    """
    Клас для зберігання інформації про контакт.
    """

    def __init__(self, name: str):
        self.name = Name(name)
        self.phones: List[Phone] = []
        self.birthday: Optional[Birthday] = None

    def add_phone(self, phone: str) -> None:
        """
        Додає номер телефону до контакту.
        """

        existing = self.find_phone(phone)
        if existing:
            # Блокуємо можливість додавати дублікати телефонів
            raise EntityAlreadyExists()

        self.phones.append(Phone(phone))

    def remove_phone(self, phone: str) -> None:
        """
        Видаляє номер телефону з контакту.
        """
        phone_to_remove = self.find_phone(phone)

        if phone_to_remove:
            self.phones.remove(phone_to_remove)

    def edit_phone(self, old_phone: str, new_phone: str) -> None:
        """
        Редагує номер телефону.
        """
        phone_to_edit = self.find_phone(old_phone)

        if not phone_to_edit:
            raise ValueError("Phone number not found.")

        if self.find_phone(new_phone):
            raise EntityAlreadyExists()

        phone_to_edit.value = Phone(new_phone).value

    def find_phone(self, phone: str) -> Optional[Phone]:
        """
        Шукає номер телефону у контакті.
        """
        for item in self.phones:
            if item.value == phone:
                return item

        return None

    def add_birthday(self, birthday: str) -> None:
        self.birthday = Birthday(birthday)

    def show_birthday(self) -> str:
        if not self.birthday:
            return "Birthday not set"
        return self.birthday.value.strftime("%d.%m.%Y")

    def __str__(self) -> str:
        phones = (
            "; ".join(phone.value for phone in self.phones)
            if self.phones
            else "no phones"
        )

        bday = (
            self.birthday.value.strftime("%d.%m.%Y") if self.birthday else "no birthday"
        )

        return f"Contact name: {self.name.value}, phones: {phones}, birthday: {bday}"


class AddressBook(UserDict):
    """
    Клас для зберігання адресної книги.
    """

    def add_record(self, record: Record) -> None:
        """
        Додає запис до адресної книги.
        """
        self.data[record.name.value] = record

    def find(self, value: str, key: str = "name") -> Optional[Record]:
        """
        Пошук контакту за ім'ям або телефоном.

        Args:
            value: Значення для пошуку.
            key: Поле пошуку ("name" або "phone").

        Returns:
            Record або None.
        """

        if key == "name":
            return self.data.get(value)

        if key == "phone":
            for record in self.data.values():
                for phone in record.phones:
                    if phone.value == value:
                        return record

        return None

    def delete(self, name: str) -> None:
        """
        Видаляє запис за ім'ям.
        """
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self) -> List[Dict[str, str]]:
        """
        Повертає список користувачів,
        яких потрібно привітати протягом наступних 7 днів.
        """
        result = []
        today = datetime.today().date()

        for record in self.data.values():
            if not record.birthday:
                continue

            bday = record.birthday.value

            # День народження в цьому або наступному році якщо вже пройшло
            # Плюс перехватимо потенційний варіант  29 лютого на невисокосному році
            try:
                bday = bday.replace(year=today.year)
            except ValueError:
                bday = bday.replace(year=today.year, day=28)

            if bday < today:
                bday = bday.replace(year=today.year + 1)

            # Перевірка, чи в межах 7 днів
            if 0 <= (bday - today).days <= 7:
                week_day = datetime.weekday(bday)

                # Перенос з вихідних на понеділок
                if week_day == 5 or week_day == 6:
                    bday += timedelta(days=(7 - week_day))

                result.append(
                    {"name": record.name.value, "birthday": bday.strftime("%d.%m.%Y")}
                )

        return result


def input_error(func):
    """
    Декоратор для обробки помилок введення користувача.
    """

    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except EntityAlreadyExists:
            return "Value already exists!"

        except ValueError as e:
            return str(e)

        except KeyError:
            return "Contact not found."

        except IndexError:
            return "Enter the argument for the command."

    return inner


def parse_input(user_input: str) -> Tuple[str, List[str]]:
    """
    Розбирає введений користувачем рядок на команду та аргументи.

    Args:
        user_input: Рядок введений користувачем.

    Returns:
        tuple: (команда, список аргументів)
    """
    parts = user_input.strip().split()
    if not parts:
        return "", []

    command = parts[0].lower()
    args = parts[1:]
    return command, args

def save_data(book, filename: str = "addressbook.pkl") -> None:
    """
    Зберігає AddressBook у файл.
    """
    with open(filename, "wb") as f:
        pickle.dump(book, f)

def load_data(filename: str = "addressbook.pkl") -> AddressBook:
    """
    Завантажує AddressBook з файлу.
    Якщо файлу немає — створює нову книгу.
    """
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()       

@input_error
def add_contact(args: List[str], book: AddressBook) -> str:
    """
    Додає новий контакт у словник.
    """

    try:
        name, phone, *_ = args
    except ValueError:
        raise ValueError("Give me name and phone please")

    record = book.find(name)
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    else:
        message = "Contact updated."

    if phone:
        record.add_phone(phone)

    return message


@input_error
def change_contact(args: List[str], book: AddressBook) -> str:
    """
    Змінює існуючий контакт.
    """
    try:
        name, old_phone, new_phone, *_ = args
    except ValueError:
        raise ValueError("Give me name, old_phone and new_phone please")

    record = book.find(name)

    if not record:
        raise KeyError

    record.edit_phone(old_phone, new_phone)
    return "Contact updated."


@input_error
def show_phone(args: List[str], book: AddressBook) -> str:
    """
    Повертає телефон за ім'ям.
    """
    try:
        name, *_ = args
    except ValueError:
        raise ValueError("Give me name please")

    record = book.find(name)

    if not record:
        raise KeyError

    phones = (
        "; ".join(phone.value for phone in record.phones)
        if record.phones
        else "no phones"
    )

    return phones


@input_error
def show_all(book: AddressBook) -> str:
    """
    Повертає всі контакти.
    """
    if not book.data:
        return "No contacts"

    return "\n".join(str(r) for r in book.data.values())


@input_error
def add_birthday(args, book: AddressBook):
    try:
        name, date, *_ = args
    except ValueError:
        raise ValueError("Give me name and date please")

    record = book.find(name)

    if not record:
        raise KeyError

    record.add_birthday(date)
    return "Birthday added."


@input_error
def show_birthday(args, book: AddressBook):
    try:
        name, *_ = args
    except ValueError:
        raise ValueError("Give me name please")

    record = book.find(name)

    if not record:
        raise KeyError

    return record.show_birthday()


@input_error
def birthdays(book: AddressBook) -> str:
    data = book.get_upcoming_birthdays()

    if not data:
        return "No upcoming birthdays"

    return "\n".join(f"{i['name']}: {i['birthday']}" for i in data)


def main():
    book = load_data()
    print("Welcome to the assistant bot!")

    try:
        while True:
            user_input = input("Enter a command: ")
            command, args = parse_input(user_input)

            if command in ["close", "exit"]:
                print("Good bye!")
                break

            elif command == "hello":
                print("How can I help you?")

            elif command == "add":
                print(add_contact(args, book))

            elif command == "change":
                print(change_contact(args, book))

            elif command == "phone":
                print(show_phone(args, book))

            elif command == "all":
                print(show_all(book))

            elif command == "add-birthday":
                print(add_birthday(args, book))

            elif command == "show-birthday":
                print(show_birthday(args, book))

            elif command == "birthdays":
                print(birthdays(book))

            else:
                print("Invalid command.")

    finally:
        save_data(book)

if __name__ == "__main__":
    main()
