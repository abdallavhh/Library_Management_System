from flet import (
    Page,Image, AppBar, Icon, Text, IconButton, PopupMenuButton, PopupMenuItem,
    ThemeMode, MainAxisAlignment, CrossAxisAlignment,Alignment, colors, Container,
    Column, Row, TextField, ElevatedButton, icons, DataTable, DataColumn,
    DataCell, DataRow, Divider, border, Tabs, Tab, Dropdown, dropdown, app
)
import sqlite3
import pandas as pd
from fpdf import FPDF
import datetime
import os

# Database setup remains the same
conn = sqlite3.connect('library.db', check_same_thread=False)
cursor = conn.cursor()

# Table creation remains the same
cursor.execute('''CREATE TABLE IF NOT EXISTS Books (
                    BookID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Title TEXT NOT NULL,
                    Author TEXT NOT NULL,
                    CopiesAvailable INTEGER NOT NULL
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Name TEXT NOT NULL,
                    Email TEXT UNIQUE NOT NULL,
                    Phone TEXT,
                    MembershipDate TEXT
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS BorrowRecords (
                    RecordID INTEGER PRIMARY KEY AUTOINCREMENT,
                    UserID INTEGER,
                    BookID INTEGER,
                    BorrowDate TEXT,
                    ReturnDate TEXT,
                    Status TEXT,
                    FOREIGN KEY (UserID) REFERENCES Users(UserID),
                    FOREIGN KEY (BookID) REFERENCES Books(BookID)
                )''')
cursor.execute('''CREATE TABLE IF NOT EXISTS Reservations (
                    ReservationID INTEGER PRIMARY KEY AUTOINCREMENT,
                    UserID INTEGER,
                    BookID INTEGER,
                    ReservationDate TEXT,
                    Status TEXT,
                    FOREIGN KEY (UserID) REFERENCES Users(UserID),
                    FOREIGN KEY (BookID) REFERENCES Books(BookID)
                )''')
conn.commit()

def main(page: Page):
    page.title = "Library Management System"
    page.window.width = 1500  # Increased width for better layout
    page.window.height = 700
    page.window.top = 10
    page.scroll = "auto"  # Changed to auto for better scrolling
    page.theme_mode = ThemeMode.DARK
    page.vertical_alignment = MainAxisAlignment.START  # Changed from CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER

    page.appbar = AppBar(
        bgcolor=colors.BLACK38,
        title=Text('Library Management System'),
        center_title=True,
        leading=Icon(icons.HOME),
        actions=[
            IconButton(icons.NOTIFICATIONS),
            PopupMenuButton(
                items=[
                    PopupMenuItem(text='Settings'),
                    PopupMenuItem(text='About Us'),
                    PopupMenuItem(text='Logout')
                ]
            )
        ]
    )

    img = Image(src='library.jpg')
    status_text = Text(value="", size=16)
    
    def format_date():
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # All your existing functions (add_book, add_user, etc.) remain largely the same
    # Adding try-except blocks for better error handling
    def add_book(e):
        try:
            title = title_field.value.strip()
            author = author_field.value.strip()
            copies = copies_field.value.strip()

            if not all([title, author, copies]):
                status_text.value = "Please fill all fields!"
                status_text.color = "red"
                page.update()
                return

            copies = int(copies)
            cursor.execute('INSERT INTO Books (Title, Author, CopiesAvailable) VALUES (?, ?, ?)', 
                         (title, author, copies))
            conn.commit()
            status_text.value = f"Book '{title}' added successfully!"
            status_text.color = "green"
            refresh_books_table()
            # Clear fields after successful addition
            title_field.value = ""
            author_field.value = ""
            copies_field.value = ""
            page.update()
        except ValueError:
            status_text.value = "Copies must be a number!"
            status_text.color = "red"
            page.update()
        except Exception as e:
            status_text.value = f"Error adding book: {str(e)}"
            status_text.color = "red"
            page.update()

    # Function to add a user
    def add_user(e):
        try:
            name = name_field.value.strip()
            email = email_field.value.strip()
            phone = phone_field.value.strip()
            
            if not all([name, email]):
                status_text.value = "Name and Email are required!"
                status_text.color = "red"
                page.update()
                return
                
            # Use current date as membership date
            membership_date = format_date()
            
            cursor.execute('INSERT INTO Users (Name, Email, Phone, MembershipDate) VALUES (?, ?, ?, ?)', 
                         (name, email, phone, membership_date))
            conn.commit()
            status_text.value = f"User '{name}' added successfully!"
            status_text.color = "green"
            refresh_users_table()
            # Clear fields after successful addition
            name_field.value = ""
            email_field.value = ""
            phone_field.value = ""
            page.update()
        except Exception as e:
            status_text.value = f"Error adding user: {str(e)}"
            status_text.color = "red"
            page.update()
    
    # Function to add a borrow record
    def add_borrow(e):
        try:
            user_id = user_id_field.value.strip()
            book_id = book_id_field.value.strip()
            
            if not all([user_id, book_id]):
                status_text.value = "User ID and Book ID are required!"
                status_text.color = "red"
                page.update()
                return
                
            user_id = int(user_id)
            book_id = int(book_id)
            
            # Check if book is available
            cursor.execute('SELECT CopiesAvailable FROM Books WHERE BookID = ?', (book_id,))
            result = cursor.fetchone()
            if not result:
                status_text.value = f"Book with ID {book_id} not found!"
                status_text.color = "red"
                page.update()
                return
                
            copies_available = result[0]
            if copies_available <= 0:
                status_text.value = f"Book with ID {book_id} is not available!"
                status_text.color = "red"
                page.update()
                return
                
            # Check if user exists
            cursor.execute('SELECT UserID FROM Users WHERE UserID = ?', (user_id,))
            if not cursor.fetchone():
                status_text.value = f"User with ID {user_id} not found!"
                status_text.color = "red"
                page.update()
                return
                
            # Add borrow record
            borrow_date = format_date()
            status = "Borrowed"
            
            cursor.execute('INSERT INTO BorrowRecords (UserID, BookID, BorrowDate, ReturnDate, Status) VALUES (?, ?, ?, ?, ?)', 
                         (user_id, book_id, borrow_date, "", status))
            
            # Update book copies
            cursor.execute('UPDATE Books SET CopiesAvailable = CopiesAvailable - 1 WHERE BookID = ?', (book_id,))
            conn.commit()
            
            status_text.value = f"Book borrowed successfully!"
            status_text.color = "green"
            refresh_borrow_records_table()
            refresh_books_table()
            # Clear fields after successful addition
            user_id_field.value = ""
            book_id_field.value = ""
            page.update()
        except ValueError:
            status_text.value = "User ID and Book ID must be numbers!"
            status_text.color = "red"
            page.update()
        except Exception as e:
            status_text.value = f"Error adding borrow record: {str(e)}"
            status_text.color = "red"
            page.update()
    
    # Function to return a book
    def return_book(e):
        try:
            record_id = return_record_id_field.value.strip()
            
            if not record_id:
                status_text.value = "Record ID is required!"
                status_text.color = "red"
                page.update()
                return
                
            record_id = int(record_id)
            
            # Check if borrow record exists and is not already returned
            cursor.execute('SELECT BookID, Status FROM BorrowRecords WHERE RecordID = ?', (record_id,))
            result = cursor.fetchone()
            if not result:
                status_text.value = f"Borrow record with ID {record_id} not found!"
                status_text.color = "red"
                page.update()
                return
                
            book_id, current_status = result
            if current_status == "Returned":
                status_text.value = f"Book has already been returned!"
                status_text.color = "red"
                page.update()
                return
                
            # Update borrow record
            return_date = format_date()
            cursor.execute('UPDATE BorrowRecords SET ReturnDate = ?, Status = ? WHERE RecordID = ?', 
                         (return_date, "Returned", record_id))
            
            # Update book copies
            cursor.execute('UPDATE Books SET CopiesAvailable = CopiesAvailable + 1 WHERE BookID = ?', (book_id,))
            conn.commit()
            
            status_text.value = f"Book returned successfully!"
            status_text.color = "green"
            refresh_borrow_records_table()
            refresh_books_table()
            # Clear fields after successful operation
            return_record_id_field.value = ""
            page.update()
        except ValueError:
            status_text.value = "Record ID must be a number!"
            status_text.color = "red"
            page.update()
        except Exception as e:
            status_text.value = f"Error returning book: {str(e)}"
            status_text.color = "red"
            page.update()
    
    # Function to add a reservation
    def add_reservation(e):
        try:
            user_id = reservation_user_id_field.value.strip()
            book_id = reservation_book_id_field.value.strip()
            
            if not all([user_id, book_id]):
                status_text.value = "User ID and Book ID are required!"
                status_text.color = "red"
                page.update()
                return
                
            user_id = int(user_id)
            book_id = int(book_id)
            
            # Check if book exists
            cursor.execute('SELECT BookID FROM Books WHERE BookID = ?', (book_id,))
            if not cursor.fetchone():
                status_text.value = f"Book with ID {book_id} not found!"
                status_text.color = "red"
                page.update()
                return
                
            # Check if user exists
            cursor.execute('SELECT UserID FROM Users WHERE UserID = ?', (user_id,))
            if not cursor.fetchone():
                status_text.value = f"User with ID {user_id} not found!"
                status_text.color = "red"
                page.update()
                return
                
            # Add reservation record
            reservation_date = format_date()
            status = "Reserved"
            
            cursor.execute('INSERT INTO Reservations (UserID, BookID, ReservationDate, Status) VALUES (?, ?, ?, ?)', 
                         (user_id, book_id, reservation_date, status))
            conn.commit()
            
            status_text.value = f"Book reserved successfully!"
            status_text.color = "green"
            refresh_reservations_table()
            # Clear fields after successful addition
            reservation_user_id_field.value = ""
            reservation_book_id_field.value = ""
            page.update()
        except ValueError:
            status_text.value = "User ID and Book ID must be numbers!"
            status_text.color = "red"
            page.update()
        except Exception as e:
            status_text.value = f"Error making reservation: {str(e)}"
            status_text.color = "red"
            page.update()
    
    # Function to cancel a reservation
    def cancel_reservation(e):
        try:
            reservation_id = cancel_reservation_id_field.value.strip()
            
            if not reservation_id:
                status_text.value = "Reservation ID is required!"
                status_text.color = "red"
                page.update()
                return
                
            reservation_id = int(reservation_id)
            
            # Check if reservation exists
            cursor.execute('SELECT ReservationID FROM Reservations WHERE ReservationID = ?', (reservation_id,))
            if not cursor.fetchone():
                status_text.value = f"Reservation with ID {reservation_id} not found!"
                status_text.color = "red"
                page.update()
                return
                
            # Update reservation status
            cursor.execute('UPDATE Reservations SET Status = ? WHERE ReservationID = ?', 
                         ("Cancelled", reservation_id))
            conn.commit()
            
            status_text.value = f"Reservation cancelled successfully!"
            status_text.color = "green"
            refresh_reservations_table()
            # Clear fields after successful operation
            cancel_reservation_id_field.value = ""
            page.update()
        except ValueError:
            status_text.value = "Reservation ID must be a number!"
            status_text.color = "red"
            page.update()
        except Exception as e:
            status_text.value = f"Error cancelling reservation: {str(e)}"
            status_text.color = "red"
            page.update()

    # Functions for exporting reports
    def export_books_pdf(e):
        try:
            cursor.execute('SELECT BookID, Title, Author, CopiesAvailable FROM Books')
            books = cursor.fetchall()
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.cell(200, 10, txt="Books Report", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Generated on: {format_date()}", ln=True, align='C')
            pdf.ln(10)
            
            # Add table headers
            col_width = 40
            pdf.cell(col_width, 10, "Book ID", 1)
            pdf.cell(col_width * 2, 10, "Title", 1)
            pdf.cell(col_width, 10, "Author", 1)
            pdf.cell(col_width, 10, "Copies Available", 1)
            pdf.ln()
            
            # Add data rows
            for book in books:
                pdf.cell(col_width, 10, str(book[0]), 1)
                pdf.cell(col_width * 2, 10, book[1], 1)
                pdf.cell(col_width, 10, book[2], 1)
                pdf.cell(col_width, 10, str(book[3]), 1)
                pdf.ln()
            
            # Save PDF
            filename = f"books_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(filename)
            status_text.value = f"PDF report saved as {filename}"
            status_text.color = "green"
            page.update()
        except Exception as e:
            status_text.value = f"Error generating PDF: {str(e)}"
            status_text.color = "red"
            page.update()
    
    def export_books_excel(e):
        try:
            cursor.execute('SELECT BookID, Title, Author, CopiesAvailable FROM Books')
            books = cursor.fetchall()
            
            df = pd.DataFrame(books, columns=["Book ID", "Title", "Author", "Copies Available"])
            
            # Save Excel file
            filename = f"books_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            
            status_text.value = f"Excel report saved as {filename}"
            status_text.color = "green"
            page.update()
        except Exception as e:
            status_text.value = f"Error generating Excel: {str(e)}"
            status_text.color = "red"
            page.update()
    
    def export_users_pdf(e):
        try:
            cursor.execute('SELECT UserID, Name, Email, Phone, MembershipDate FROM Users')
            users = cursor.fetchall()
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.cell(200, 10, txt="Users Report", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Generated on: {format_date()}", ln=True, align='C')
            pdf.ln(10)
            
            # Add table headers
            col_width = 40
            pdf.cell(col_width / 2, 10, "ID", 1)
            pdf.cell(col_width, 10, "Name", 1)
            pdf.cell(col_width * 1.5, 10, "Email", 1)
            pdf.cell(col_width, 10, "Phone", 1)
            pdf.cell(col_width, 10, "Membership Date", 1)
            pdf.ln()
            
            # Add data rows
            for user in users:
                pdf.cell(col_width / 2, 10, str(user[0]), 1)
                pdf.cell(col_width, 10, user[1], 1)
                pdf.cell(col_width * 1.5, 10, user[2], 1)
                pdf.cell(col_width, 10, user[3], 1)
                pdf.cell(col_width, 10, user[4], 1)
                pdf.ln()
            
            # Save PDF
            filename = f"users_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(filename)
            status_text.value = f"PDF report saved as {filename}"
            status_text.color = "green"
            page.update()
        except Exception as e:
            status_text.value = f"Error generating PDF: {str(e)}"
            status_text.color = "red"
            page.update()
    
    def export_users_excel(e):
        try:
            cursor.execute('SELECT UserID, Name, Email, Phone, MembershipDate FROM Users')
            users = cursor.fetchall()
            
            df = pd.DataFrame(users, columns=["User ID", "Name", "Email", "Phone", "Membership Date"])
            
            # Save Excel file
            filename = f"users_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            
            status_text.value = f"Excel report saved as {filename}"
            status_text.color = "green"
            page.update()
        except Exception as e:
            status_text.value = f"Error generating Excel: {str(e)}"
            status_text.color = "red"
            page.update()
    
    def export_borrows_pdf(e):
        try:
            cursor.execute('''
                SELECT br.RecordID, u.Name, b.Title, br.BorrowDate, br.ReturnDate, br.Status 
                FROM BorrowRecords br
                JOIN Users u ON br.UserID = u.UserID
                JOIN Books b ON br.BookID = b.BookID
            ''')
            records = cursor.fetchall()
            
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            
            # Add title
            pdf.cell(200, 10, txt="Borrow Records Report", ln=True, align='C')
            pdf.cell(200, 10, txt=f"Generated on: {format_date()}", ln=True, align='C')
            pdf.ln(10)
            
            # Add table headers
            col_width = 30
            pdf.cell(col_width, 10, "Record ID", 1)
            pdf.cell(col_width, 10, "User Name", 1)
            pdf.cell(col_width, 10, "Book Title", 1)
            pdf.cell(col_width, 10, "Borrow Date", 1)
            pdf.cell(col_width, 10, "Return Date", 1)
            pdf.cell(col_width, 10, "Status", 1)
            pdf.ln()
            
            # Add data rows
            for record in records:
                pdf.cell(col_width, 10, str(record[0]), 1)
                pdf.cell(col_width, 10, record[1], 1)
                pdf.cell(col_width, 10, record[2], 1)
                pdf.cell(col_width, 10, record[3], 1)
                pdf.cell(col_width, 10, record[4] if record[4] else "", 1)
                pdf.cell(col_width, 10, record[5], 1)
                pdf.ln()
            
            # Save PDF
            filename = f"borrows_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
            pdf.output(filename)
            status_text.value = f"PDF report saved as {filename}"
            status_text.color = "green"
            page.update()
        except Exception as e:
            status_text.value = f"Error generating PDF: {str(e)}"
            status_text.color = "red"
            page.update()
    
    def export_borrows_excel(e):
        try:
            cursor.execute('''
                SELECT br.RecordID, u.Name, b.Title, br.BorrowDate, br.ReturnDate, br.Status 
                FROM BorrowRecords br
                JOIN Users u ON br.UserID = u.UserID
                JOIN Books b ON br.BookID = b.BookID
            ''')
            records = cursor.fetchall()
            
            df = pd.DataFrame(records, columns=["Record ID", "User Name", "Book Title", "Borrow Date", "Return Date", "Status"])
            
            # Save Excel file
            filename = f"borrows_report_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.xlsx"
            df.to_excel(filename, index=False)
            
            status_text.value = f"Excel report saved as {filename}"
            status_text.color = "green"
            page.update()
        except Exception as e:
            status_text.value = f"Error generating Excel: {str(e)}"
            status_text.color = "red"
            page.update()

    # Updated table refresh functions with proper widths
    def refresh_books_table():
        cursor.execute('SELECT BookID, Title, Author, CopiesAvailable FROM Books')
        books = cursor.fetchall()
        books_table.rows.clear()
        for book in books:
            books_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(str(book[0]))),
                    DataCell(Text(book[1])),
                    DataCell(Text(book[2])),
                    DataCell(Text(str(book[3])))
                ])
            )
        page.update()

    def refresh_users_table():
        cursor.execute('SELECT UserID, Name, Email, Phone, MembershipDate FROM Users')
        users = cursor.fetchall()
        users_table.rows.clear()
        for user in users:
            users_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(str(user[0]))),
                    DataCell(Text(user[1])),
                    DataCell(Text(user[2])),
                    DataCell(Text(user[3] if user[3] else "")),
                    DataCell(Text(user[4]))
                ])
            )
        page.update()

    def refresh_borrow_records_table():
        cursor.execute('SELECT RecordID, UserID, BookID, BorrowDate, ReturnDate, Status FROM BorrowRecords')
        records = cursor.fetchall()
        borrow_records_table.rows.clear()
        for record in records:
            borrow_records_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(str(record[0]))),
                    DataCell(Text(str(record[1]))),
                    DataCell(Text(str(record[2]))),
                    DataCell(Text(record[3])),
                    DataCell(Text(record[4] if record[4] else "")),
                    DataCell(Text(record[5]))
                ])
            )
        page.update()

    def refresh_reservations_table():
        cursor.execute('SELECT ReservationID, UserID, BookID, ReservationDate, Status FROM Reservations')
        reservations = cursor.fetchall()
        reservations_table.rows.clear()
        for reservation in reservations:
            reservations_table.rows.append(
                DataRow(cells=[
                    DataCell(Text(str(reservation[0]))),
                    DataCell(Text(str(reservation[1]))),
                    DataCell(Text(str(reservation[2]))),
                    DataCell(Text(reservation[3])),
                    DataCell(Text(reservation[4]))
                ])
            )
        page.update()

    # Input fields for Books tab
    title_field = TextField(label="Title", width=350, border_radius=10)
    author_field = TextField(label="Author", width=350, border_radius=10)
    copies_field = TextField(label="Copies Available", width=350, border_radius=10)
    delete_field = TextField(label="Book ID to Delete", width=350, border_radius=10)

    add_book_button = ElevatedButton("Add Book", on_click=add_book)
    delete_button = ElevatedButton("Delete Book", on_click=lambda e: delete_book(delete_field.value))

    # Input fields for Users tab
    name_field = TextField(label="Name", width=350, border_radius=10)
    email_field = TextField(label="Email", width=350, border_radius=10)
    phone_field = TextField(label="Phone", width=350, border_radius=10)

    add_user_button = ElevatedButton("Add User", on_click=add_user)

    # Input fields for Borrows tab
    user_id_field = TextField(label="User ID", width=250, border_radius=10)
    book_id_field = TextField(label="Book ID", width=250, border_radius=10)
    return_record_id_field = TextField(label="Record ID to Return", width=250, border_radius=10)

    add_borrow_button = ElevatedButton("Borrow Book", on_click=add_borrow)
    return_book_button = ElevatedButton("Return Book", on_click=return_book)

    # Input fields for Reservations tab
    reservation_user_id_field = TextField(label="User ID", width=250, border_radius=10)
    reservation_book_id_field = TextField(label="Book ID", width=250, border_radius=10)
    cancel_reservation_id_field = TextField(label="Reservation ID to Cancel", width=250, border_radius=10)

    add_reservation_button = ElevatedButton("Reserve Book", on_click=add_reservation)
    cancel_reservation_button = ElevatedButton("Cancel Reservation", on_click=cancel_reservation)

    def delete_book(book_id):
        try:
            book_id = int(book_id)
            cursor.execute('DELETE FROM Books WHERE BookID = ?', (book_id,))
            conn.commit()
            status_text.value = f"Book with ID {book_id} deleted successfully!"
            status_text.color = "green"
            refresh_books_table()
            delete_field.value = ""
            page.update()
        except ValueError:
            status_text.value = "Book ID must be a number!"
            status_text.color = "red"
            page.update()
        except Exception as e:
            status_text.value = f"Error deleting book: {str(e)}"
            status_text.color = "red"
            page.update()

    # Tables with adjusted widths
    books_table = DataTable(
        columns=[
            DataColumn(Text("ID")),
            DataColumn(Text("Title")),
            DataColumn(Text("Author")),
            DataColumn(Text("Copies Available"))
        ],
        rows=[],
        width=800,  # Increased width
        column_spacing=20
    )

    users_table = DataTable(
        columns=[
            DataColumn(Text("ID")),
            DataColumn(Text("Name")),
            DataColumn(Text("Email")),
            DataColumn(Text("Phone")),
            DataColumn(Text("Membership Date"))
        ],
        rows=[],
        width=800,
        column_spacing=20
    )

    borrow_records_table = DataTable(
        columns=[
            DataColumn(Text("Record ID")),
            DataColumn(Text("User ID")),
            DataColumn(Text("Book ID")),
            DataColumn(Text("Borrow Date")),
            DataColumn(Text("Return Date")),
            DataColumn(Text("Status"))
        ],
        rows=[],
        width=800,
        column_spacing=20
    )

    reservations_table = DataTable(
        columns=[
            DataColumn(Text("Reservation ID")),
            DataColumn(Text("User ID")),
            DataColumn(Text("Book ID")),
            DataColumn(Text("Reservation Date")),
            DataColumn(Text("Status"))
        ],
        rows=[],
        width=800,
        column_spacing=20
    )

    # Initial table refresh
    refresh_books_table()
    refresh_users_table()
    refresh_borrow_records_table()
    refresh_reservations_table()

    # Tabs with adjusted layouts
    books_tab = Container(
        content=Column(
            [
                Row(
                    [
                        Column([Text("Add a New Book", size=18, weight="bold"), title_field, 
                               author_field, copies_field, add_book_button]),
                        Column([Text("Delete a Book", size=18, weight="bold"), delete_field, delete_button])
                    ],
                    spacing=40
                ),
                Divider(height=20),
                Text("Books List", size=18, weight="bold"),
                Container(content=books_table, height=300, border=border.all(1, colors.GREY_400), 
                         border_radius=10, padding=10)
            ],
            spacing=15
        ),
        padding=20
    )

    users_tab = Container(
        content=Column(
            [
                Row(
                    [
                        Column([Text("Add a New User", size=18, weight="bold"), name_field, 
                               email_field, phone_field, add_user_button])
                    ],
                    spacing=40
                ),
                Divider(height=20),
                Text("Users List", size=18, weight="bold"),
                Container(content=users_table, height=300, border=border.all(1, colors.GREY_400), 
                         border_radius=10,

        )],
            spacing=15
        ),
        padding=20
    )

    borrows_tab = Container(
        content=Column(
            [
                Row(
                    [
                        Column([Text("Borrow a Book", size=18, weight="bold"), user_id_field, 
                               book_id_field, add_borrow_button]),
                        Column([Text("Return a Book", size=18, weight="bold"), return_record_id_field, 
                               return_book_button])
                    ],
                    spacing=40
                ),
                Divider(height=20),
                Text("Borrow Records", size=18, weight="bold"),
                Container(content=borrow_records_table, height=300, border=border.all(1, colors.GREY_400), 
                         border_radius=10, padding=10)
            ],
            spacing=15
        ),
        padding=20
    )

    reservations_tab = Container(
        content=Column(
            [
                Row(
                    [
                        Column([Text("Reserve a Book", size=18, weight="bold"), reservation_user_id_field, 
                               reservation_book_id_field, add_reservation_button]),
                        Column([Text("Cancel a Reservation", size=18, weight="bold"), 
                               cancel_reservation_id_field, cancel_reservation_button])
                    ],
                    spacing=40
                ),
                Divider(height=20),
                Text("Reservations List", size=18, weight="bold"),
                Container(content=reservations_table, height=300, border=border.all(1, colors.GREY_400), 
                         border_radius=10, padding=10)
            ],
            spacing=15
        ),
        padding=20
    )

    reports_tab = Container(
        content=Column(
            [
                Text("Generate Reports", size=18, weight="bold"),
                Row(
                    [
                        Column([
                            Text("Books Reports", size=16),
                            ElevatedButton("Export Books to PDF", on_click=export_books_pdf),
                            ElevatedButton("Export Books to Excel", on_click=export_books_excel)
                        ]),
                        Column([
                            Text("Users Reports", size=16),
                            ElevatedButton("Export Users to PDF", on_click=export_users_pdf),
                            ElevatedButton("Export Users to Excel", on_click=export_users_excel)
                        ]),
                        Column([
                            Text("Borrow Records Reports", size=16),
                            ElevatedButton("Export Borrows to PDF", on_click=export_borrows_pdf),
                            ElevatedButton("Export Borrows to Excel", on_click=export_borrows_excel)
                        ])
                    ],
                    spacing=40,
                    alignment=MainAxisAlignment.CENTER
                ),
                Divider(height=20),
                Text("Status", size=16, weight="bold"),
                status_text
            ],
            spacing=15,
            alignment=CrossAxisAlignment.CENTER
        ),
        padding=20
    )

    # Create and display tabs
    tabs = Tabs(
        selected_index=0,
        animation_duration=300,
        tabs=[
            Tab(text="Books", content=books_tab),
            Tab(text="Users", content=users_tab),
            Tab(text="Borrows", content=borrows_tab),
            Tab(text="Reservations", content=reservations_tab),
            Tab(text="Reports", content=reports_tab)
        ],
        width=850
    )

    # Add tabs to page
    page.add(Container(tabs, padding=20))

    # Add status text at the bottom
    page.add(Container(status_text, padding=10))
    
    page.add(img)
    
if __name__ == "__main__":
    app(target=main)
