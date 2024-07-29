"""Get the posts from reddit and populate the database with the appropriate textual data"""

import sqlite3 as sq
# import json
import os
from bs4 import BeautifulSoup
from tqdm import tqdm
import requests

# possibly want the permalink to be a PRIMARY KEY so we don't have duplicate data in database
def database_creation(database_name) -> sq.Connection:
    """Makes the database and associated tables"""
    connection = sq.connect(database_name)
    cur = connection.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS posts(permalink TEXT, link TEXT, title TEXT, `link-host` TEXT, `author-id` TEXT)")
    cur.close()
    connection.commit()
    return connection

def add_posts(conn : sq.Connection, post):
    """Inserts data into the database as specified in `database_creation`"""
    SQL = "INSERT INTO posts(`permalink`, `link`, `title`, `link-host`, `author-id`) VALUES (?, ?, ?, ?, ?)"
    cur = conn.cursor()
    cur.execute(SQL, post)
    conn.commit()
    return cur.lastrowid

def get_next_url(soup : BeautifulSoup):
    """Gets the next URL cursor from the current page"""
    next_cursor = soup.find("shreddit-post", {"more-posts-cursor" : True})
    return next_cursor["more-posts-cursor"] if next_cursor is not None else None

def get_details(page : requests.Response):
    """Get the details from Reddit using beautifulsoup"""
    soup = BeautifulSoup(page.content, "html.parser")
    article = soup.find_all("article")
    ret = {}
    for a in article:
        art = {}
        details = a.find("shreddit-post")
        if (details != None):
            if (details["post-type"] != "link"):
                continue
            link = a.find("a", class_="post-link")
            if (link != None):
                art["permalink"] = details["permalink"]
                ret[details["permalink"]] = {
                    "link" : link["href"],
                    "title" : a["aria-label"],
                    "link-host" : details["domain"],
                    "author-id" :  details["author-id"],
                }
    return ret, get_next_url(soup), len(article)

DB_NAME = "data.db"

con = sq.connect(DB_NAME) if os.path.exists(DB_NAME) else database_creation(DB_NAME)

URL = "https://www.reddit.com/svc/shreddit/community-more-posts/new/?after=dDNfMWVkcGZ5Zg%3D%3D&t=DAY&name=politics&feedLength=153"
test_page = requests.get(URL, timeout=100)

# print(json.dumps(get_details(test_page),sort_keys=True, indent=4))

test_details = get_details(test_page)

# for key in tqdm(test_details.keys()):
#     detail = test_details[key]
#     last_row_id = add_posts(con, (key, detail['link'], detail['title'], detail["link-host"], detail["author-id"]))
#     # print(f"last row id: {last_row_id}")



# https://www.reddit.com/svc/shreddit/community-more-posts/hot/?after=dDNfMWVlOWl5cw%3D%3D&t=DAY&name=politics&feedLength=128
# https://www.reddit.com/svc/shreddit/community-more-posts/hot/?after=dDNfMWVlZjFyaA%3D%3D&t=DAY&name=politics&feedLength=103
# https://www.reddit.com/svc/shreddit/community-more-posts/hot/?after=dDNfMWVlZjFyaA%3D%3D&t=DAY&name=politics&feedLength=103