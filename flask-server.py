#!/usr/bin/env python3

from restaurant_crud import RestaurantCRUD
from flask import Flask, render_template, request, url_for, redirect, jsonify, flash

app = Flask(__name__)
crud = RestaurantCRUD()
#
@app.route("/")
@app.route("/restaurant")
def restaurant():
    restaurants = crud.get_all_restaurants()
    return render_template("restaurant.html", restaurants=restaurants)

@app.route("/restaurant/new", methods=["GET", "POST"])
def newRestaurant():
    if request.method == "POST":
        data = request.form
        if data["action"] == "CREATE":
            crud.create_restaurant(data["name"])
            flash("New Restaurant Created!")
        return redirect(url_for('restaurant'))
    else:
        return render_template("restaurant_op.html", restaurant="", op="add")

@app.route("/restaurant/<int:r_id>/edit", methods=["GET", "POST"])
def editRestaurant(r_id):
    if request.method == "POST":
        data = request.form
        if data["action"] == "UPDATE":
            crud.update_restaurant_name(r_id, data["name"])
        return redirect(url_for('restaurant'))
    else:
        r = crud.get_restaurant(r_id)
        return render_template("restaurant_op.html", restaurant=r, op="edit")

@app.route("/restaurant/<int:r_id>/delete", methods=["GET", "POST"])
def deleteRestaurant(r_id):
    if request.method == "POST":
        data = request.form
        if data["action"] == "DELETE":
            crud.delete_restaurant(r_id)
        return redirect(url_for('restaurant'))
    else:
        r = crud.get_restaurant(r_id)
        return render_template("restaurant_op.html", restaurant=r, op="delete")

@app.route("/restaurant/<int:r_id>/", methods =["GET", "POST"])
def restaurantMenuItem(r_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_rest_menu_items(r_id)
    courses =[]
    for i in m:
        courses.append(i.course)
    courses = list(set(courses))

    return render_template("menu.html", courses=courses, restaurant=r, items=m)

@app.route("/restaurant/<int:r_id>/<int:m_id>/edit", methods=["GET", "POST"])
def editMenuItem(r_id, m_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_menu_item(r.id, m_id)
    if request.method == "POST":
        data = request.form
        if data["action"] == "UPDATE":
            crud.update_menu_item(r.id, m.id, data["name"], data["course"], data["description"], data["price"])
        return redirect(url_for('restaurantMenuItem', r_id=r.id))
    else:
        return render_template("menuitem_op.html", restaurant=r, menu_item=m, op="edit")

@app.route("/restaurant/<int:r_id>/<int:m_id>/delete", methods=["GET", "POST"])
def deleteMenuItem(r_id, m_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_menu_item(r.id, m_id)
    if request.method == "POST":
        data = request.form
        if data["action"] == "DELETE":
            crud.delete_menu_item(r.id, m.id)
        return redirect(url_for('restaurantMenuItem', r_id=r.id))
    else:
        return render_template("menuitem_op.html", restaurant=r, menu_item=m, op="delete")

@app.route("/restaurant/<int:r_id>/new", methods=["GET", "POST"])
def newMenuItem(r_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_rest_menu_items(r_id)
    if request.method == "POST":
        data = request.form
        if data["action"] == "CREATE":
            crud.create_menu_item(r.id, data["name"], data["description"], data["course"], data["price"])
            flash("New menu item created!")
        return redirect(url_for('restaurantMenuItem', r_id=r.id))
    else:
        return render_template("menuitem_op.html", restaurant=r, menu_item='', op="add")

@app.route("/restaurant/<int:r_id>/menu/JSON", methods=["GET"])
def getRestaurantMenuItemJSON(r_id):
    menu_items = crud.get_rest_menu_items(r_id)
    print(menu_items[0])
    return jsonify(MenuItems=[{
        "name":i.name,
        "price":i.price,
        "course":i.course,
        "description":i.description
        } for i in menu_items])

if __name__ == "__main__":
    app.secret_key = "super secret key"
    app.debug = True
    app.run(host="0.0.0.0", port=8000)