#!/usr/bin/env python3

from restaurant_crud import RestaurantCRUD
from flask import Flask, render_template, request, url_for, redirect, jsonify, flash
import bleach

# Oauth2 imports
from flask import session as login_session
from flask import make_response
import string, random
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2, json, requests

app = Flask(__name__)
crud = RestaurantCRUD()
#

@app.route("/login", methods=["GET", "POST"])
def showLogin():
    state = "".join(random.choice(string.ascii_letters + string.digits) for x in range(32))
    login_session["state"] = state
    data = request.form
    if request.method == "POST":
        return redirect(url_for("restaurant"))
    return render_template("login.html", STATE=state)

@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = crud.getUserID(data["email"])
    if not user_id:
        user_id = crud.createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return jsonify(output={"body": output})
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