from flask import Flask, render_template, request, redirect
from flaskwebgui import FlaskUI
import sqlite3
from datetime import datetime
from os import remove

db = sqlite3.connect("data.db", check_same_thread=False)
cur = db.cursor()

app = Flask(__name__)

ui = FlaskUI(app=app,server='flask', width=1000, height=700)

osdate = datetime.now().strftime("%Y-%m-%d")
GENRE = []
gnr = cur.execute("SELECT * FROM genres")
for rec in gnr:
    GENRE.append(rec[1])


@app.route("/")
def index():
    return render_template("index.html", genres=GENRE, date=osdate)


@app.route("/search", methods=["GET"])
def search():
    page = request.args.get("page")
    if page == "library":
        title = cur.execute("SELECT * FROM library WHERE book LIKE ? OR author LIKE ? OR id LIKE ?", (("%" + request.args.get("title") + "%"),("%" + request.args.get("title") + "%"),("%" + request.args.get("title") + "%")))
        rec = []
        for x in title:
            rec.append(x)
        return render_template("search.html", title=rec, page=page)
    elif page == "members":
        title = cur.execute("SELECT * FROM members WHERE id LIKE ? OR name LIKE ? OR dateofjoining LIKE ?", (("%" + request.args.get("title") + "%"),("%" + request.args.get("title") + "%"), ("%" + request.args.get("title") + "%")))
        rec = []
        for x in title:
            rec.append(x)
        return render_template("search.html", title=rec, page=page)
    return render_template("error.html", message="Could not perform search!")


@app.route("/add", methods=["POST"])
def add():
    book = request.form.get("book")
    if not book:
        return render_template("error.html", message="Book name missing")
    author = request.form.get("author")
    if not author:
        return render_template("error.html", message="Author missing")
    genre = request.form.get("genre")
    print(genre)
    if not genre:
        return render_template("error.html", message="Genre missing")
    if genre not in GENRE:
        return render_template("error.html", message="Invalid genre")

    cur.execute("INSERT INTO library (book, author, genre, lent) VALUES(?, ?, ?, ?)", (book, author, genre, "No"))
    db.commit()
    return redirect("/library")


@app.route("/library")
def library():
    lib = cur.execute("SELECT * FROM library")
    rec = []
    for x in lib:
        rec.append(x)
    
    return render_template("library.html", library=rec)


@app.route("/delete", methods=["POST"])
def delete():
    ident = request.form.get("id")
    if ident:
        cur.execute("DELETE FROM library WHERE id = ?", (ident,))
        cur.execute("DELETE FROM issuedbooks WHERE id = ?", (ident,))
        db.commit()
    return redirect("/library")


@app.route("/update", methods=["POST"])
def update():
    ident1 = request.form.get("id")
    if ident1:
        cur.execute("DELETE FROM issuedbooks WHERE id = ?",(ident1,))
        cur.execute("UPDATE library SET lent = (CASE WHEN lent = 'Yes' THEN 'No' WHEN lent = 'No' THEN 'Yes' END) WHERE id= ?", (ident1,))
        cur.execute("UPDATE members SET book1 = (CASE WHEN book1 = ? THEN null END), book2 = (CASE WHEN book2 = ? THEN null END)", (ident1,ident1))
        db.commit()
        cur.execute("SELECT * FROM library WHERE id = ?", (ident1,))
        rec = cur.fetchone()
    return render_template("/book.html", book=rec)

@app.route("/genres")
def genre():
    genre = cur.execute("SELECT * FROM genres")
    rec = []
    for x in genre:
        rec.append(x)
    return render_template("genres.html", gen=rec)


@app.route("/addgenre", methods=["POST"])
def addgenre():
    genre = request.form.get("genre")
    cur.execute("INSERT INTO genres (genre) VALUES(?)", (genre,))
    db.commit()
    return redirect("/genres")

@app.route("/delgenre", methods=["POST"])
def delgenre():
    ident3 = request.form.get("id")
    cur.execute("DELETE FROM genres WHERE sno = ?", (ident3,))
    db.commit()
    return redirect("/genres")

@app.route("/book", methods=["GET","POST"])
def book():
    id = request.form.get("id")
    info = cur.execute("SELECT * FROM library WHERE id = ?", (id,))
    rec = None
    for x in info:
        rec = x
    cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(id,))
    mid = cur.fetchone()
    return render_template("book.html", book = rec, genres=GENRE, mid=mid)

@app.route("/updatebook", methods = ["POST"])
def updatebook():
    id = request.form.get("id")
    book = request.form.get("book")
    author = request.form.get("author")
    genre = request.form.get("genre")
    summary = request.form.get("summary")
    addlinfo = request.form.get("addlinfo")
    rec = [id, book, author, genre, summary, addlinfo]
    cur.execute("UPDATE library SET book = ?, author = ?, genre = ?, summary = ?, addlinfo = ? WHERE id = ?", (book, author, genre, summary, addlinfo, id))
    db.commit()
    return render_template("book.html", book=rec, genres=GENRE)


@app.route("/members")
def members(): 
    cur.execute("SELECT * FROM members")
    rec = cur.fetchall()
    rec2 = []
    mem=[]
    for x in rec:
        k = []
        for y in x:
            k.append(y)
        rec2.append(k)
    for x in rec2:
        if x[3] != None:
            x[3] = 'static/images/'+x[3]
        mem.append(x)
    return render_template("members.html", mem=mem)


@app.route("/addmember", methods=["POST"])
def addmember():
    date = request.form.get("doj")
    name =  request.form.get("name")
    photo = request.files['photo']
    if not photo:
        cur.execute("INSERT INTO members (name, dateofjoining) VALUES(?, ?)", (name, date))
        db.commit()
    else:
        cur.execute("SELECT id FROM members ORDER BY id DESC LIMIT 1")
        rec = cur.fetchone()
        no = None
        if rec is not None:
            no = rec[0]
            no = no+1
        x = photo.filename
        y = x.split(".")
        newName = None
        if rec is None:
            newName = "1" + "." + y[-1]
        else:
            newName = str(no) + "." + y[-1]
        photo.save("static/images/"+newName)
        cur.execute("INSERT INTO members (name, dateofjoining, photo) VALUES(?, ?, ?)", (name, date, newName))
        db.commit()
    return redirect("/members")

@app.route("/delmember", methods=["POST"])
def delmemeber():
    id = request.form.get("id")
    cur.execute("SELECT * FROM members WHERE id = ?", (id,))
    rec = cur.fetchone()
    cur.execute("DELETE FROM members where id = ?", (id,))
    cur.execute("UPDATE library SET lent = 'No' WHERE id = (SELECT id FROM issuedbooks WHERE memberid = ?)", (id,))
    cur.execute("DELETE FROM issuedbooks where memberid = ?", (id,))
    db.commit()
    if rec[3] != None:
        try:
            path = 'static/images/' + rec[3]
            remove(path)
        except FileNotFoundError:
            pass
    return redirect("/members")

@app.route("/member", methods = ["POST"])
def member():
    id = request.form.get("id")
    cur.execute("SELECT * FROM members WHERE id = ?", (id,))
    rec = cur.fetchone()
    mem=[]
    for x in rec:
        mem.append(x)
    if mem[3] != None:
            mem[3] = 'static/images/'+mem[3]
    return render_template("member.html", member = mem)

@app.route("/updatemember", methods = ["POST"])
def updatemember():
    id = request.form.get("id")
    name = request.form.get("name")
    photo = request.files['photo']
    cur.execute("SELECT * FROM members WHERE id = ?", (id,))
    rec = cur.fetchone()
    if not photo:
        cur.execute("UPDATE members SET name = ? WHERE id = ?", (name, id))
        db.commit()
    else:
        id =  rec[0]
        x = photo.filename
        y = x.split(".")
        newName = str(id)+"."+y[-1]
        try:
            remove("static/images/"+rec[3])
        except:
            pass
        photo.save("static/images/"+newName)
        cur.execute("UPDATE members SET name = ?, photo = ? WHERE id = ?", (name, newName, id))
        db.commit()
    cur.execute("SELECT * FROM members WHERE id = ?", (id,))
    rec  = cur.fetchone()
    mem=[]
    for x in rec:
        mem.append(x)
    if mem[3] != None:
            mem[3] = 'static/images/'+mem[3]
    return render_template("member.html", member = mem)

@app.route("/issue", methods = ["POST"])
def issue():
    mid = request.form.get("member_id")
    bid = request.form.get("book_id")
    doi = request.form.get("doi")
    dor = request.form.get("dor")
    cur.execute("SELECT * FROM members WHERE id = ?",(mid,))
    rec = cur.fetchone()
    cur.execute("SELECT * FROM library WHERE id = ?", (bid,))
    rec2 = cur.fetchone()
    if rec2[4] == "Yes":
        return render_template("error.html", message="The book has already been lent to someone else!")
    if rec[4] == None:
        cur.execute("UPDATE members SET book1 = ? WHERE id = ?", (bid,mid))
        cur.execute("UPDATE library SET lent = 'Yes' WHERE id= ?;", (bid,))
        cur.execute("INSERT INTO issuedbooks (id, book, memberid, member, doi, dor) VALUES(?, ?, ?, ?, ?, ?)", (bid, rec2[1], mid, rec[2], doi, dor))
        db.commit()
        cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(mid,))
        mid = cur.fetchone()
        return render_template("book.html", book=rec2, genres=GENRE, mid=mid)
    elif rec[5] == None:
        cur.execute("UPDATE members SET book2 = ? WHERE id = ?", (bid,mid))
        cur.execute("UPDATE library SET lent = 'Yes' WHERE id= ?;", (bid,))
        db.commit()
        cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(mid,))
        mid = cur.fetchone()
        return render_template("book.html", book=rec2, genres=GENRE, mid=mid)
    if rec[4] != None and rec[5] != None:
        return render_template("error.html", message="Book can not be issued. Issue limit for member reached!")
    return render_template("error.html", message="Error in issuing. Try again!")

@app.route("/issuedbooks")
def issuedbooks():
    cur.execute("SELECT * FROM issuedbooks")
    rec = cur.fetchall()
    return render_template("issuedbooks.html", rec = rec)

if __name__ == '__main__':
    #app.run(port=5000)
    ui.run()
