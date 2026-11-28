import sqlite3
import markupsafe
import secrets

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

def check_csrf():
    if "csrf_token" not in request.form:
        abort(403)
    if request.form["csrf_token"] != session["csrf_token"]:
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

def get_selected_classes(all_classes):
    classes = []
    for entry in request.form.getlist("classes"):
        if entry:
            class_title, class_value = entry.split(":")
            if class_title not in all_classes:
                abort(403)
            if class_value not in all_classes[class_title]:
                abort(403)
            classes.append((class_title, class_value))
    return classes

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
    classes = recipes.get_classes(recipe_id)
    reviews = recipes.get_reviews(recipe_id)
    average_grade = recipes.get_average_grade(recipe_id)
    return render_template("show_recipe.html", recipe=recipe,
                           classes=classes, reviews=reviews,
                           average_grade=average_grade)

@app.route("/new_recipe")
def new_recipe():
    require_login()
    classes = recipes.get_all_classes()
    return render_template("new_recipe.html", classes=classes, filled={})

@app.route("/create_recipe", methods=["POST"])
def create_recipe():
    require_login()
    check_csrf()

    title = request.form["title"].strip()
    ingredients = request.form["ingredients"].strip()
    instructions = request.form["instructions"].strip()

    all_classes = recipes.get_all_classes()
    classes = get_selected_classes(all_classes)

    errors = validate_recipe(title, ingredients, instructions)
    if errors:
        for error in errors:
            flash(error, "error")
        filled = {"title": title,
                  "ingredients": ingredients,
                  "instructions": instructions,
                  "classes": dict(classes)}
        return render_template("new_recipe.html", classes=all_classes,
                               filled=filled)

    user_id = session["user_id"]
    recipe_id = recipes.add_recipe(title, ingredients, instructions,
                                   user_id, classes)

    flash("Resepti lisätty")
    return redirect("/recipe/" + str(recipe_id))

@app.route("/edit_recipe/<int:recipe_id>")
def edit_recipe(recipe_id):
    require_login()
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] != session["user_id"]:
        abort(403)

    all_classes = recipes.get_all_classes()
    selected = {}
    for entry in recipes.get_classes(recipe_id):
        selected[entry["title"]] = entry["value"]

    return render_template("edit_recipe.html", recipe=recipe,
                           classes=all_classes, selected=selected)

@app.route("/update_recipe", methods=["POST"])
def update_recipe():
    require_login()
    check_csrf()
    recipe_id = request.form["recipe_id"]
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] != session["user_id"]:
        abort(403)

    title = request.form["title"].strip()
    ingredients = request.form["ingredients"].strip()
    instructions = request.form["instructions"].strip()

    all_classes = recipes.get_all_classes()
    classes = get_selected_classes(all_classes)

    errors = validate_recipe(title, ingredients, instructions)
    if errors:
        for error in errors:
            flash(error, "error")
        filled = {"id": recipe_id,
                  "title": title,
                  "ingredients": ingredients,
                  "instructions": instructions}
        return render_template("edit_recipe.html", recipe=filled,
                               classes=all_classes, selected=dict(classes))

    recipes.update_recipe(recipe_id, title, ingredients, instructions,
                          classes)

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
        check_csrf()
        if "remove" in request.form:
            recipes.remove_recipe(recipe_id)
            return redirect("/")
        else:
            return redirect("/recipe/" + str(recipe_id))

@app.route("/create_review", methods=["POST"])
def create_review():
    require_login()
    check_csrf()

    recipe_id = request.form["recipe_id"]
    recipe = recipes.get_recipe(recipe_id)
    if not recipe:
        abort(404)
    if recipe["user_id"] == session["user_id"]:
        abort(403)

    grade = request.form["grade"]
    if grade not in ["1", "2", "3", "4", "5"]:
        abort(403)

    comment = request.form["comment"].strip()
    if not comment or len(comment) > 1000:
        flash("VIRHE: kommentin pitää olla 1–1000 merkkiä pitkä", "error")
        return redirect("/recipe/" + str(recipe_id))

    user_id = session["user_id"]
    recipes.add_review(recipe_id, user_id, int(grade), comment)

    flash("Arvio lisätty")
    return redirect("/recipe/" + str(recipe_id))

@app.route("/register")
def register():
    return render_template("register.html", filled={})

@app.route("/create", methods=["POST"])
def create():
    username = request.form["username"].strip()
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
            session["csrf_token"] = secrets.token_hex(16)
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