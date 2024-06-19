from flask import Flask, render_template, request, redirect, send_file
from flaskwebgui import FlaskUI
import sqlite3
from datetime import datetime
from os import remove, listdir, makedirs, path
from shutil import rmtree
from zipfile import ZipFile
import pickle

db = sqlite3.connect("data.db", check_same_thread=False)
cur = db.cursor()

makedirs("import", exist_ok=True)

makedirs("themes", exist_ok=True)

makedirs("images", exist_ok=True)

app = Flask(__name__)

ui = FlaskUI(app=app,server='flask', width=1000, height=700)

app.config["TEMPLATES_AUTO_RELOAD"] = True

osdate = datetime.now().strftime("%Y-%m-%d")

cur.execute("SELECT preference FROM preferences WHERE id = 1")
theme = cur.fetchone()[0]
if theme != "default":
    final = []
    urls = listdir('themes/'+theme)
    for x in urls:
        url = 'themes/' + theme + '/' + x
        final.append(url)
    theme=final
print(theme)

@app.route("/")
def index():
    GENRE = []
    gnr = cur.execute("SELECT * FROM genres")
    for rec in gnr:
        GENRE.append(rec[1])
    return render_template("index.html", genres=GENRE, date=osdate, theme=theme)


@app.route("/search", methods=["GET"])
def search():
    page = request.args.get("page")
    if page == "library":
        title = cur.execute("SELECT * FROM library WHERE book LIKE ? OR author LIKE ? OR id LIKE ?", (("%" + request.args.get("title") + "%"),("%" + request.args.get("title") + "%"),("%" + request.args.get("title") + "%")))
        rec = []
        for x in title:
            rec.append(x)
        return render_template("search.html", title=rec, page=page, theme=theme)
    elif page == "members":
        title = cur.execute("SELECT * FROM members WHERE id LIKE ? OR name LIKE ? OR dateofjoining LIKE ?", (("%" + request.args.get("title") + "%"),("%" + request.args.get("title") + "%"), ("%" + request.args.get("title") + "%")))
        rec = []
        for x in title:
            rec.append(x)
        return render_template("search.html", title=rec, page=page, theme=theme)
    return render_template("error.html", message="Could not perform search!", theme=theme)


@app.route("/add", methods=["POST"])
def add():
    GENRE = []
    gnr = cur.execute("SELECT * FROM genres")
    for rec in gnr:
        GENRE.append(rec[1])
    book = request.form.get("book")
    if not book:
        return render_template("error.html", message="Book name missing", theme=theme)
    author = request.form.get("author")
    if not author:
        return render_template("error.html", message="Author missing", theme=theme)
    genre = request.form.get("genre")
    if not genre:
        return render_template("error.html", message="Genre missing", theme=theme)
    if genre not in GENRE:
        return render_template("error.html", message="Invalid genre", theme=theme)

    cur.execute("INSERT INTO library (book, author, genre, lent) VALUES(?, ?, ?, ?)", (book, author, genre, "No"))
    db.commit()
    return redirect("/library")


@app.route("/library")
def library():
    lib = cur.execute("SELECT * FROM library")
    rec = []
    for x in lib:
        rec.append(x)
    
    return render_template("library.html", library=rec, theme=theme)


@app.route("/delete", methods=["POST"])
def delete():
    ident = request.form.get("id")
    if ident:
        cur.execute("DELETE FROM library WHERE id = ?", (ident,))
        cur.execute("DELETE FROM issuedbooks WHERE id = ?", (ident,))
        cur.execute("UPDATE members SET book1 = (CASE WHEN book1 = ? THEN null END), book2 = (CASE WHEN book2 = ? THEN null END)", (ident,ident))
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
        cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(str(id),))
        mid = cur.fetchone()
    return render_template("/book.html", book=rec, theme=theme, mid=mid)

@app.route("/genres")
def genre():
    genre = cur.execute("SELECT * FROM genres")
    rec = []
    for x in genre:
        rec.append(x)
    return render_template("genres.html", gen=rec, theme=theme)


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
    GENRE = []
    gnr = cur.execute("SELECT * FROM genres")
    for rec in gnr:
        GENRE.append(rec[1])
    id = request.form.get("id")
    info = cur.execute("SELECT * FROM library WHERE id = ?", (id,))
    rec = None
    for x in info:
        rec = x
    cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(str(id),))
    mid = cur.fetchone()
    return render_template("book.html", book = rec, genres=GENRE, mid=mid, theme=theme)

@app.route("/updatebook", methods = ["POST"])
def updatebook():
    GENRE = []
    gnr = cur.execute("SELECT * FROM genres")
    for rec in gnr:
        GENRE.append(rec[1])
    id = request.form.get("id")
    book = request.form.get("book")
    author = request.form.get("author")
    genre = request.form.get("genre")
    summary = request.form.get("summary")
    addlinfo = request.form.get("addlinfo")
    cur.execute("UPDATE library SET book = ?, author = ?, genre = ?, summary = ?, addlinfo = ? WHERE id = ?", (book, author, genre, summary, addlinfo, id))
    db.commit()
    cur.execute("SELECT * FROM library where id = ?",(id,))
    rec = cur.fetchone()
    cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(str(id),))
    mid = cur.fetchone()
    return render_template("book.html", book=rec, genres=GENRE, mid=mid, theme=theme)


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
            x[3] = 'images/'+x[3]
        mem.append(x)
    return render_template("members.html", mem=mem, theme=theme)


@app.route("/addmember", methods=["POST"])
def addmember():
    date = request.form.get("doj")
    name =  request.form.get("name")
    #photo = request.files['photo']
    #if not photo:
    cur.execute("INSERT INTO members (name, dateofjoining) VALUES(?, ?)", (name, date))
    db.commit()
    '''else:
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
        photo.save("images/"+newName)
        cur.execute("INSERT INTO members (name, dateofjoining, photo) VALUES(?, ?, ?)", (name, date, newName))
        db.commit()'''
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
            path = 'images/' + rec[3]
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
            mem[3] = 'images/'+mem[3]
    return render_template("member.html", member = mem, theme=theme)

@app.route("/updatemember", methods = ["POST"])
def updatemember():
    id = request.form.get("id")
    name = request.form.get("name")
    #photo = request.files['photo']
    #if not photo:
    cur.execute("UPDATE members SET name = ? WHERE id = ?", (name, id))
    db.commit()
    '''else:
        id =  rec[0]
        x = photo.filename
        y = x.split(".")
        newName = str(id)+"."+y[-1]
        try:
            remove("images/"+rec[3])
        except:
            pass
        photo.save("images/"+newName)
        cur.execute("UPDATE members SET name = ?, photo = ? WHERE id = ?", (name, newName, id))
        db.commit()
    cur.execute("SELECT * FROM members WHERE id = ?", (id,))
    rec  = cur.fetchone()
    mem=[]
    for x in rec:
        mem.append(x)
    if mem[3] != None:
            mem[3] = 'images/'+mem[3]'''
    cur.execute("SELECT * FROM members WHERE id = ?", (id,))
    rec = cur.fetchone()
    return render_template("member.html", theme=theme, member=rec)

@app.route("/issue", methods = ["POST"])
def issue():
    GENRE = []
    gnr = cur.execute("SELECT * FROM genres")
    for rec in gnr:
        GENRE.append(rec[1])
    mid = request.form.get("member_id")
    bid = request.form.get("book_id")
    doi = request.form.get("doi")
    dor = request.form.get("dor")
    cur.execute("SELECT * FROM members WHERE id = ?",(mid,))
    rec = cur.fetchone()
    cur.execute("SELECT * FROM library WHERE id = ?", (bid,))
    rec2 = cur.fetchone()
    if rec2[4] == "Yes":
        return render_template("error.html", message="The book has already been lent to someone else!", theme=theme)
    if rec[4] == None:
        cur.execute("UPDATE members SET book1 = ? WHERE id = ?", (bid,mid))
        cur.execute("UPDATE library SET lent = 'Yes' WHERE id= ?;", (bid,))
        cur.execute("INSERT INTO issuedbooks (id, book, memberid, member, doi, dor) VALUES(?, ?, ?, ?, ?, ?)", (bid, rec2[1], mid, rec[2], doi, dor))
        db.commit()
        cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(str(mid),))
        mid = cur.fetchone()
        cur.execute("SELECT * FROM library WHERE id = ?", (bid,))
        rec2 = cur.fetchone()
        return render_template("book.html", book=rec2, theme=theme, genres=GENRE, mid=mid)
    elif rec[5] == None:
        cur.execute("UPDATE members SET book2 = ? WHERE id = ?", (bid,mid))
        cur.execute("UPDATE library SET lent = 'Yes' WHERE id= ?;", (bid,))
        db.commit()
        cur.execute("SELECT memberid FROM issuedbooks WHERE id = ?",(str(mid),))
        mid = cur.fetchone()
        cur.execute("SELECT * FROM library WHERE id = ?", (bid,))
        rec2 = cur.fetchone()
        return render_template("book.html", theme=theme, book=rec2, genres=GENRE, mid=mid)
    if rec[4] != None and rec[5] != None:
        return render_template("error.html", theme=theme, message="Book can not be issued. Issue limit for member reached!")
    return render_template("error.html",theme=theme, message="Error in issuing. Try again!")

@app.route("/issuedbooks")
def issuedbooks():
    cur.execute("SELECT * FROM issuedbooks")
    rec = cur.fetchall()
    return render_template("issuedbooks.html", rec = rec, theme=theme)

@app.route("/impexp")
def impexp():
    if path.exists("export.zip"):
        exportpath = path.abspath("export.zip")
        return render_template("impexp.html", file=True, theme=theme, exportpath=exportpath)
    else:
        return render_template("impexp.html", file=False, theme=theme)

@app.route("/importd", methods=["POST"])
def importd():
    file = request.files['file']
    x = file.filename
    x = x.split(".")
    if x[-1] != "zip":
        return render_template("error.html", theme=theme, message = "Incorrect file format! Try again.")
    file.save("imported.zip")
    with ZipFile(file, "r") as ff:
        ff.extractall()
    xlibrary = []
    xgenres = []
    xissuedbooks = []
    xmembers = []
    data = [xlibrary, xgenres, xissuedbooks, xmembers]
    files = ["import/library.zip", "import/genres.zip", "import/issuedbooks.zip", "import/members.zip"]
    for y in range(len(data)):
        with open(files[y], "rb") as ff:
            while True:
                try:
                    k = pickle.load(ff)
                    data[y].append(k)
                except EOFError:
                    break
    cur.execute("DELETE FROM library")
    cur.execute("DELETE FROM genres")
    cur.execute("DELETE FROM issuedbooks")
    cur.execute("DELETE FROM members")
    for x in xlibrary:
        cur.execute("INSERT INTO library (id,book,author,genre,lent,summary,addlinfo) VALUES(?,?,?,?,?,?,?)", (x[0],x[1],x[2],x[3],x[4],x[5],x[6]))
        db.commit()
    for x in xmembers:
        cur.execute("INSERT INTO members (id,name,dateofjoining,photo,book1,book2) VALUES(?,?,?,?,?,?)", (x[0],x[1],x[2],x[3],x[4],x[5]))
        db.commit()
    for x in xissuedbooks:
        cur.execute("INSERT INTO issuedbooks (id,book,memberid,member,doi,dor) VALUES(?,?,?,?,?,?)", (x[0],x[1],x[2],x[3],x[4],x[5]))
        db.commit()
    for x in xgenres:
        cur.execute("INSERT INTO genres (sno,genre) VALUES(?,?)", (x[0],x[1]))
        db.commit()
    
    rmtree("import")
    makedirs("import")
    remove("imported.zip")
    return render_template("impexp.html", message="Import Successful!", theme=theme)

@app.route("/exportd")
def exportd():
    if path.exists("export.zip"):
        remove("export.zip")
    cur.execute("SELECT * FROM library")
    library = cur.fetchall()
    cur.execute("SELECT * FROM genres")
    genres = cur.fetchall()
    cur.execute("SELECT * FROM issuedbooks")
    issuedbooks = cur.fetchall()
    cur.execute("SELECT * FROM members")
    members = cur.fetchall()
    data = [library, genres, issuedbooks, members]
    files = ["import/library.zip", "import/genres.zip", "import/issuedbooks.zip", "import/members.zip"]
    imgs = listdir("images")
    for x in imgs:
        y = 'images/' + x
        imgs.remove(x)
        imgs.append(y)
    files.extend(imgs)
    for x in range(len(data)):
        with open(files[x], "ab") as ff:
            if len(data[x]) > 0:
                for y in data[x]:
                    pickle.dump(y, ff)
    with ZipFile("export.zip", "a") as ff:
        for x in files:
            ff.write(x)
    rmtree("import")
    makedirs("import")
    return redirect("/impexp")

@app.route("/download")
def download():
    return send_file("export.zip")

@app.route("/deletefile")
def deletefile():
    if path.exists("export.zip"):
        remove("export.zip")
    return redirect("/impexp")

@app.route("/settings")
def settings():
    themes = listdir("themes")
    cur.execute("SELECT preference FROM preferences WHERE id = 1")
    sel = cur.fetchone()[0]
    return render_template("settings.html", themes=themes, sel=sel, theme=theme)

@app.route("/updatesettings", methods=["POST"])
def updatesettings():
    xtheme = request.form.get("theme")
    if xtheme:
        cur.execute("UPDATE preferences SET preference = ? WHERE id = 1", (xtheme,))
        db.commit()
        themes = listdir("themes")
        cur.execute("SELECT preference FROM preferences WHERE id = 1")
        sel = cur.fetchone()[0]
        return render_template("settings.html", themes=themes, sel=sel, theme=theme)
    return render_template("error.html", message="No theme provided!", theme=theme)

@app.route("/addtheme", methods=["POST"])
def addtheme():
    xtheme = request.files['theme']
    if xtheme.filename.split(".")[-1] != "zip":
        return render_template("error.html", theme=theme, message="Wrong file provided! Try again. Only .zip files allowed.")
    xtheme.save(xtheme.filename)
    with ZipFile(xtheme.filename, "r") as ff:
        ff.extractall('themes/')
    remove(xtheme.filename)
    return redirect("/settings")
    
@app.route("/deltheme", methods=["POST"])
def deltheme():
    xtheme = request.form.get("theme")
    if xtheme:
        if xtheme == "invalid":
            return render_template("error.html", message="Select Valid Theme", theme=theme)
        if xtheme == "default":
            return render_template("error.html", theme=theme, message="Default theme can not be deleted!")
        cur.execute("SELECT preference FROM preferences WHERE id = 1")
        sel = cur.fetchone()[0]
        if xtheme == sel:
            cur.execute("UPDATE preferences SET preference = 'default' WHERE id = 1")
            db.commit()
        rmtree('themes/'+xtheme)
        return redirect("/settings")
    return render_template("error.html", message="Select valid theme!", theme=theme)
    

if __name__ == '__main__':
    #app.run(port=5000, debug=True)
    ui.run()
