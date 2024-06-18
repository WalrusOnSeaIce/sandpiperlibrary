# sandpiperlibrary
It is a webapp/ software that can be used to manage personal library or a collection of books. The software may be useful for smaller libraries as well.

It has features like adding and deleting books, adding and deleting members, issuing books to members, managing book returns from members(through Change status option), updating information about books and members and searching through the list of members and books by id, name, author etc.
You can add and change profile photos of the members and even see a list of the issued books. The app is easy to use.

The app has been written in Flask, HTML and CSS, and uses an SQLite database.


# compiling the app
pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" app.py

# db schema
CREATE TABLE library (id INTEGER, book TEXT NOT NULL, author TEXT NOT NULL, genre TEXT, lent TEXT NOT NULL, summary TEXT, addlinfo TEXT, PRIMARY KEY(id));
CREATE TABLE genres (sno INTEGER, genre TEXT NOT NULL, PRIMARY KEY(sno));
CREATE TABLE members (id INTEGER, name TEXT NOT NULL, dateofjoining DATE NOT NULL, photo TEXT, book1 TEXT, book2 TEXT, PRIMARY KEY(id));
CREATE TABLE issuedbooks (id INTEGER, book TEXT NOT NULL, memberid TEXT NOT NULL, member TEXT NOT NULL, doi DATE NOT NULL, dor DATE NOT NULL);
CREATE TABLE preferences (id INTEGER, option TEXT, preference TEXT, PRIMARY KEY(id));

# installer creation command
pyinstaller -w -F --add-data "templates;templates" --add-data "static;static" --add-data "db;db" --add-data "themes;themes" --add-data "images;images" --add-data "import;import" --onefile --icon "icon-path" app.py