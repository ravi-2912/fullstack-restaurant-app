#!/usr/bin/env python3

from restaurant_crud import RestaurantCRUD
from flask import Flask, render_template, request, url_for, redirect, jsonify, flash
import bleach

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
        # store form data
        data = request.form

        # check which button is clicked - either CREATE or CANCEL
        if data["action"] == "CREATE":
            # clean data
            rest_data = bleach.clean(data["name"])
            # perform create operation on database
            crud.create_restaurant(rest_data)
            # flash message to inform user
            flash("New Restaurant {} Created!".format(rest_data))

        # redirect to home page for both action of either CREATE or CANCEL
        return redirect(url_for('restaurant'))
    else: # else GET request
        return render_template("restaurant_op.html", restaurant="", op="add")

@app.route("/restaurant/<int:r_id>/edit", methods=["GET", "POST"])
def editRestaurant(r_id):
    if request.method == "POST":
        data = request.form

        # check which button is clicked - either UPDATE or CANCEL
        if data["action"] == "UPDATE":
            rest_data = bleach.clean(data["name"])
            crud.update_restaurant_name(r_id, rest_data)
            flash("Restaurant {} Updated!".format(rest_data))

        return redirect(url_for('restaurant'))
    else:
        r = crud.get_restaurant(r_id)
        return render_template("restaurant_op.html", restaurant=r, op="edit")

@app.route("/restaurant/<int:r_id>/delete", methods=["GET", "POST"])
def deleteRestaurant(r_id):
    if request.method == "POST":
        data = request.form

        # check which button is clicked - either DELETE or CANCEL
        if data["action"] == "DELETE":
            name = crud.get_restaurant(r_id)
            crud.delete_restaurant(r_id)
            flash("Restaurant {} Deleted!".format(name))

        return redirect(url_for('restaurant'))
    else:
        r = crud.get_restaurant(r_id)
        return render_template("restaurant_op.html", restaurant=r, op="delete")

@app.route("/restaurant/<int:r_id>/", methods =["GET", "POST"])
def restaurantMenuItem(r_id):
    # read restaurant and its menu items from database
    r = crud.get_restaurant(r_id)
    m = crud.get_rest_menu_items(r_id)

    # collect all courses provided by restaurant
    courses =[]
    for i in m:
        # prepare a course list
        courses.append(i.course)

    # get unique set of courses
    courses = list(set(courses))

    return render_template("menu.html", courses=courses, restaurant=r, items=m)

@app.route("/restaurant/<int:r_id>/<int:m_id>/edit", methods=["GET", "POST"])
def editMenuItem(r_id, m_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_menu_item(r.id, m_id)
    m_all = crud.get_rest_menu_items(r_id)

    # prepare course list
    courses = []
    for i in m_all:
        courses.append(i.course)
    courses = list(set(courses))

    if request.method == "POST":
        data = request.form

        # check if button submit is UPDATE or CANCEL
        if data["action"] == "UPDATE":
            item_name = bleach.clean(data["name"])
            item_desc = bleach.clean(data["description"])
            item_price = bleach.clean(data["price"])
            item_course = bleach.clean(data["course"])

            # check and update the new-course to item_course
            if item_course == "OTHER":
                new_course = bleach.clean(data["new-course"])
                # update the item_course to value new-course
                item_course = new_course if item_course == "OTHER" else item_course

            crud.update_menu_item(r.id, m.id, item_name, item_course, item_desc, item_price)
            flash("Menu Item {} Updated!".format(item_name))
        return redirect(url_for('restaurantMenuItem', r_id=r.id))
    else:
        return render_template("menuitem_op.html", restaurant=r, courses=courses, item=m, op="edit")

@app.route("/restaurant/<int:r_id>/<int:m_id>/delete", methods=["GET", "POST"])
def deleteMenuItem(r_id, m_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_menu_item(r.id, m_id)
    if request.method == "POST":
        data = request.form
        if data["action"] == "DELETE":
            crud.delete_menu_item(r.id, m.id)
            flash("Menu Item {} Deleted!".format(m.name))
        return redirect(url_for('restaurantMenuItem', r_id=r.id))
    else:
        return render_template("menuitem_op.html", restaurant=r, item=m, op="delete")

@app.route("/restaurant/<int:r_id>/new", methods=["GET", "POST"])
def newMenuItem(r_id):
    r = crud.get_restaurant(r_id)
    m = crud.get_rest_menu_items(r_id)

    # get all courses
    courses =[]
    for i in m:
        courses.append(i.course)
    courses = list(set(courses))

    if request.method == "POST":
        data = request.form
        if data["action"] == "CREATE":
            item_name = bleach.clean(data["name"])
            item_desc = bleach.clean(data["description"])
            item_price = bleach.clean(data["price"])
            course = bleach.clean(data["course"])
            item_course = bleach.clean(data["course"])

            # check and update the new-course to item_course
            if item_course == "OTHER":
                new_course =bleach.clean(data["new-course"])
                item_course = new_course if item_course == "OTHER" else item_course

            crud.create_menu_item(r.id, item_name, item_desc, item_course, item_price)
            flash("New Menu Item {} Created!".format(item_name))
        return redirect(url_for('restaurantMenuItem', r_id=r.id))
    else:
        return render_template("menuitem_op.html", restaurant=r, courses=courses, item='', op="add")

@app.route("/restaurant/<int:r_id>/menu/JSON", methods=["GET"])
def getRestaurantMenuItemJSON(r_id):
    menu_items = crud.get_rest_menu_items(r_id)
    return jsonify(MenuItems=[{
        "name":i.name,
        "price":i.price,
        "course":i.course,
        "description":i.description
        } for i in menu_items])

if __name__ == "__main__":
    # super secure key for flash messaging
    app.secret_key = "super secret key"
    # debug mode
    app.debug = True
    app.run(host="0.0.0.0", port=8000)