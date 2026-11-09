import db

def add_recipe(title, ingredients, instructions, user_id):
    sql = """INSERT INTO recipes (title, ingredients, instructions, user_id)
             VALUES (?, ?, ?, ?)"""
    db.execute(sql, [title, ingredients, instructions, user_id])

def get_recipes():
    sql = "SELECT id, title FROM recipes ORDER BY id DESC"
    return db.query(sql)