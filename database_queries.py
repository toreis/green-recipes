
import json
import sqlite3


def insert_recipe_URL(URL):
    with conn:
        cursor.execute("""INSERT INTO recipes (recipe_URL) VALUES (?)""", (URL,))


def update_recipe_URL(URL, recipe_id):
    with conn:
        cursor.execute(
            """UPDATE recipes SET recipe_URL = (?) WHERE recipe_id = (?)""",
            (URL, recipe_id),
        )


def update_recipe(recipe, recipe_id):
    with conn:
        cursor.execute(
            """UPDATE recipes SET recipe = (?) WHERE recipe_id = (?)""",
            (json.dumps(recipe), recipe_id),
        )


def update_recipe_co2(recipe, recipe_id):
    with conn:
        cursor.execute(
            """UPDATE recipes SET recipe_co2 = (?) WHERE recipe_id = (?)""",
            (json.dumps(recipe), recipe_id),
        )


def get_recipe_by_id(recipe_id, co2=False):
    if co2 is False:
        query = "SELECT recipe FROM recipes WHERE recipe_id = {}".format(recipe_id)
    else:
        query = "SELECT recipe_co2 FROM recipes WHERE recipe_id = {}".format(recipe_id)

    cursor.execute(query)
    recipe = cursor.fetchone()[0]
    if recipe is not None:
        recipe = json.loads(recipe)

    return recipe


def get_URL_by_id(recipe_id):
    cursor.execute(
        "SELECT recipe_URL FROM recipes WHERE recipe_id = {}".format(recipe_id)
    )
    return cursor.fetchone()[0]


def get_all_by_id(recipe_id):
    cursor.execute("SELECT * FROM recipes WHERE recipe_id = {}".format(recipe_id))
    return cursor.fetchone()


def get_max_id():
    cursor.execute("SELECT COALESCE(MAX(recipe_id), 0) FROM recipes")
    return cursor.fetchone()[0]


def delete_recipe():
    with conn:
        cursor.execute(
            """UPDATE recipes SET recipe = (?) WHERE recipe_id > 65000""", (None,)
        )


def update_autoincrement(x):
    with conn:
        cursor.execute("""UPDATE sqlite_sequence SET seq = (?)""", (x,))


def delete_entry(recipe_id):
    with conn:
        cursor.execute("""DELETE FROM recipes WHERE recipe_id = ?""", (recipe_id))


conn = sqlite3.connect("recipe_DB.db")
cursor = conn.cursor()


# cursor.execute("""CREATE TABLE IF NOT EXISTS recipes (
#                     recipe_id integer PRIMARY KEY autoincrement,
#                     recipe_URL text,
#                     recipe text,
#                     recipe_co2 text
#                     )""")