import json
import os
import sqlite3


def build():
    with open("chars.json") as f:
        chars = json.load(f)
    if os.path.exists("chars.db"):
        os.remove("chars.db")
    with sqlite3.connect("chars.db") as conn:
        cs = conn.cursor()
        cs.execute(
            '''
            CREAT TABLE Chars(
                id INT PRIMARY KEY,
                name_jp TEXT,
                name_cn TEXT,
                gw_page TEXT
            )''')
        cs.execute(
            '''
            CREAT TABLE Nicknames(
                nickname TEXT PRIMARY KEY,
                id INT
            )''')
        for idx in chars.keys():
            idnum = int(idx)
            charinfo = chars[idx]
            cs.execute(
                "INSERT INTO Chars (id, name_jp, name_cn, gw_page) VALUE(?,?,?,?)",
                (idnum, charinfo["name_jp"], charinfo["name_cn"], charinfo["gw_page"]))
            for nickname in charinfo["nicknames"]:
                cs.execute("INSTER INTO Nicknames (nickname, id) VALUE(?,?)",
                           (nickname, idnum))
        conn.commit()


if __name__ == "__main__":
    build()
