import sys
import psycopg2
import random
import itemdata
from faker import Faker


def db_populate(n=100, script_path=None, add_users=True, add_items=True, add_reviews=True, add_likes=True, url=None):
    if (url is None):
        db = DBConnector(dbname="postgres", user="postgres", host="localhost", pw="****")
    else:
        db = DBConnector(url=url)

    if (script_path is not None):
        db.execute_script(script_path)

    # Instantiate data generator
    gen = DataGenerator()

    # Password is 1234 for all acounts
    password = "$2a$10$0OwHhC5Pyu4E9aOwjQpSG.FdrgZa2wN.6FJFRusdgAt6OuvhO50gu"
    # --------- Add users ---------
    base_sql_insert = ("INSERT INTO Accounts (username, password, email, status) VALUES "
                       + build_empty_sql_insert(4))

    for i in range(n):
        u = gen.create_user_profile()
        db.cursor.execute(base_sql_insert, (u["user"], password, u["email"], "Active"))

    print("Sucessfully create %i user accounts" % n)
    db.commit()
    print("Successfully insert new user accounts")

    # --------- Add items ---------
    # Obtain list of user IDs
    db.cursor.execute("SELECT accountid FROM Accounts")
    uid = [row[0] for row in db.cursor.fetchall()]

    # Obtain list of categories
    db.cursor.execute("SELECT * FROM categories")
    cats = [row[0] for row in db.cursor.fetchall()]

    # Generate and insert item entries
    base_sql_insert = ("INSERT INTO Items (title, description, price, seller, catname) VALUES "
                       + build_empty_sql_insert(5))
    for i in range(n):
        item = gen.create_item()
        itemdesc = "I'm selling {}. This is my {}. Hope you like it!".format(
            item["catname"].lower(), item["title"].lower())

        db.cursor.execute(base_sql_insert,
                          (item["title"], itemdesc, random.randint(1, 1000), random.choice(uid), random.choice(cats)))

    db.commit()
    print("Successfully insert new items")

    # --------- Add images ---------
    # Obtain list of item ids
    db.cursor.execute("SELECT DISTINCT itemid, title FROM Items")
    items = db.cursor.fetchall()

    # Generate and insert image entries
    base_sql_img_insert = "INSERT INTO Images (itemid, imgurl, imgno) VALUES " + build_empty_sql_insert(3)

    for i in range(n):
        item = random.choice(items)
        items.remove(item)

        for inum in range(random.randint(1, 4)):
            # Image titles are of the format (adj noun). The img url is created from the noun only.
            try:
                db.cursor.execute(base_sql_img_insert, (item[0], gen.create_imgurl(item[1].split(" ")[-1], inum), inum))
            except:
                print(item)

    db.commit()
    print("Successfully insert new images")

    # --------- Add likes ---------
    # Obtain list of user IDs
    db.cursor.execute("SELECT accountid FROM Accounts")
    uid = [row[0] for row in db.cursor.fetchall()]

    # Obtain list of item ids
    db.cursor.execute("SELECT itemid FROM Items")
    items = [row[0] for row in db.cursor.fetchall()]

    # Generate and insert like entries
    base_sql_like_insert = "INSERT INTO Likes (likerid, itemid) VALUES " + build_empty_sql_insert(2)

    for item in items:
        numLikers = random.randint(0, len(uid))
        likers = random.sample(uid, k=numLikers)
        for liker in likers:
            db.cursor.execute(base_sql_like_insert, (liker, item))

    db.commit()
    print("Successfully insert new likes")

    # ------------- Closing connection ---------------
    print("Closing connection...")
    db.close()


def build_empty_sql_insert(n_attr):
    if n_attr <= 0:
        return "()"
    # Leave out the last extra ','
    return "(" + ("%s," * n_attr)[:-1] + ")"


class DBConnector:
    def __init__(self, dbname=None, user=None, host=None, pw=None, url=None):
        str_connection = "dbname = '{}' user = '{}' host = '{}' password = '{}' port = '5432'".format(dbname, user,
                                                                                                      host, pw)
        try:
            if (url is None):
                self.conn = psycopg2.connect(str_connection)
            else:
                self.conn = psycopg2.connect(url)
            print("Successfully Connected to DB")
        except psycopg2.DatabaseError as ex:
            print("Connection to database failed: {}".format(ex))
            sys.exit(1)
        self.cursor = self.conn.cursor()

    def commit(self):
        '''
        Commits current changes and instantiates a new DB cursor
        '''
        self.conn.commit()
        self.cursor = self.conn.cursor()

    def execute_script(self, path):
        self.cursor.execute(open(path, "r").read())
        self.commit()
        print("Successfully executed script at %s" % path)
        
    def close(self):
        self.cursor.close()
        self.conn.close()



class DataGenerator:
    def __init__(self):
        self.fake = Faker()

    def create_user_profile(self):
        gen = self.fake.simple_profile()
        return {"user": gen["username"],
                "email": gen["mail"]}

    def create_item(self):
        return {"catname": random.choice(itemdata.CATEGORIES),
                "title": (random.choice(itemdata.POLITE_ADJECTIVES).capitalize()
                          + " " + random.choice(itemdata.ANIMALS))}

    def create_imgurl(self, itemtype, imgno):
        return "https://loremflickr.com/400/240/" + itemtype + "?random=" + str(imgno)
