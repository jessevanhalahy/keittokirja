import sqlite3
import markupsafe

from flask import Flask
from flask import abort, flash, redirect, render_template, request, session

import config
import recipes
import users

app = Flask(__name__)
app.secret_key = config.secret_key
def require_login():
    if "user_id" not in session:
        abort(403)

@app.template_filter()
def show_lines(content):
    content = str(markupsafe.escape(content))
    content = content.replace("\n", "<br />")
    return markupsafe.Markup(content)

def validate_recipe(title, ingredients, instructions):
    errors = []
    if not title or len(title) > 100:
        errors.append("VIRHE: reseptin nimen täytyy olla 1–100 merkkiä pitkä")
    if not ingredients or len(ingredients) > 2000:
        errors.append("VIRHE: lista aineksista täytyy olla 1–2000 merkkiä pitkä")
    if not instructions or len(instructions) > 5000:
        errors.append("VIRHE: valmistusohjeen täytyy olla 1–5000 merkkiä pitkä")
    return errors

@app.route("/")
def index():
    all_recipes = recipes.get_recipes()
    return render_template("index.html", recipes=all_recipes)

@app.route("/find_recipe")
def find_recipe():
    query = request.args.get("query")
    if query:
        results = recipes.find_recipes(query)
    else:
        query = ""
        results = []
    return render_template("find_recipe.html", query=query, results=results)

@app.route("/user/<int:user_id>")
def show_user(user_id):
    user = users.get_user(user_id)
    if not user:
        abort(404)
    user_recipes = users.get_recipes(user_id)
    recipe_count = users.get_recipe_count(user_id)
    return render_template("show_user.html", user=user,
                           recipes=user_recipes, recipe_count=recipe_count)

@app.route("/recipe/<int:recipe_id>")
def show_recipe(recipe_id):
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    return render_template("show_recipe.html", recipe=recipe)

@app.route("/new_recipe")
def new_recipe():
    require_login()
    return render_template("new_recipe.html", filled={})

@app.route("/create_recipe", methods=["POST"])
def create_recipe():
    require_login()

    title = request.form["title"]
    ingredients = request.form["ingredients"]
    instructions = request.form["instructions"]

    errors = validate_recipe(title, ingredients, instructions)
    if errors:
        for error in errors:
            flash(error, "error")
        filled = {"title": title,
                  "ingredients": ingredients,
                  "instructions": instructions}
        return render_template("new_recipe.html", filled=filled)

    user_id = session["user_id"]
    recipes.add_recipe(title, ingredients, instructions, user_id)

    flash("Resepti lisätty")
    return redirect("/")

@app.route("/edit_recipe/<int:recipe_id>")
def edit_recipe(recipe_id):
    require_login()
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] != session["user_id"]:
        abort(403)
    return render_template("edit_recipe.html", recipe=recipe)

@app.route("/update_recipe", methods=["POST"])
def update_recipe():
    require_login()
    recipe_id = request.form["recipe_id"]
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] != session["user_id"]:
        abort(403)

    title = request.form["title"]
    ingredients = request.form["ingredients"]
    instructions = request.form["instructions"]

    errors = validate_recipe(title, ingredients, instructions)
    if errors:
        for error in errors:
            flash(error)
        filled = {"id": recipe_id,
                  "title": title,
                  "ingredients": ingredients,
                  "instructions": instructions}
        return render_template("edit_recipe.html", recipe=filled)

    recipes.update_recipe(recipe_id, title, ingredients, instructions)

    flash("Muutokset tallennettu")
    return redirect("/recipe/" + str(recipe_id))

@app.route("/remove_recipe/<int:recipe_id>", methods=["GET", "POST"])
def remove_recipe(recipe_id):
    require_login()
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] != session["user_id"]:
        abort(403)

    if request.method == "GET":
        return render_template("remove_recipe.html", recipe=recipe)

    if request.method == "POST":
        if "remove" in request.form:
            recipes.remove_recipe(recipe_id)
            return redirect("/")
        else:
            return redirect("/recipe/" + str(recipe_id))

@app.route("/register")
def register():
    return render_template("register.html", filled={})

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]

    errors = []
    if not username or len(username) > 20:
        errors.append("VIRHE: tunnuksen täytyy olla 1–20 merkkiä pitkä")
    if not password1 or len(password1) > 100:
        errors.append("VIRHE: salasanan täytyy olla 1–100 merkkiä pitkä")
    if password1 != password2:
        errors.append("VIRHE: salasanat eivät ole samat")

    if errors:
        for error in errors:
            flash(error)
        filled = {"username": username}
        return render_template("register.html", filled=filled)

    try:
        users.create_user(username, password1)
    except sqlite3.IntegrityError:
        flash("VIRHE: tunnus on jo varattu", "error")
        filled = {"username": username}
        return render_template("register.html", filled=filled)

    flash("Tunnus luotu, voit nyt kirjautua sisään")
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user_id = users.check_login(username, password)
        if user_id:
            session["user_id"] = user_id
            session["username"] = username
            return redirect("/")
        else:
            flash("VIRHE: väärä tunnus tai salasana", "error")
            return redirect("/login")

@app.route("/logout")
def logout():
    if "user_id" in session:
        del session["user_id"]
        del session["username"]
    return redirect("/")