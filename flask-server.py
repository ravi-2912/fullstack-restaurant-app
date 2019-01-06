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


CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"


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

@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print ("access token received %s " % access_token)


    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (
        app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]


    # Use token to get user info from API
    userinfo_url = "https://graph.facebook.com/v2.8/me"
    '''
        Due to the formatting for the result from the server token exchange we have to
        split the token first on commas and select the first index which gives us the key : value
        for the server access token then we split it on colons to pull out the actual token value
        and replace the remaining quotes with nothing so that it can be used directly in the graph
        api calls
    '''
    print(result)
    token = result.split(',')[0].split(':')[1].replace('"', '')

    url = 'https://graph.facebook.com/v2.8/me?access_token=%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    # print "url sent for API access:%s"% url
    # print "API JSON result: %s" % result
    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    # The token must be stored in the login_session in order to properly logout
    login_session['access_token'] = token

    # Get user picture
    url = 'https://graph.facebook.com/v2.8/me/picture?access_token=%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)

    login_session['picture'] = data["data"]["url"]

    # see if user exists
    user_id = crud.getUserID(login_session['email'])
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

    flash("Now logged in as %s" % login_session['username'])
    return jsonify(output={"body": output})

def gdisconnect():
    # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        response = make_response(json.dumps('Failed to revoke token for given user.'))#, 400))
        response.headers['Content-Type'] = 'application/json'
        return response

def fbdisconnect():
    facebook_id = login_session['facebook_id']
    # The access token must me included to successfully logout
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    print(login_session)
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('restaurant'))
    else:
        flash("You are not logged in")
        return redirect(url_for('restaurant'))

@app.route("/")
@app.route("/restaurant")
def restaurant():
    restaurants = crud.get_all_restaurants()
    return render_template("restaurant.html", restaurants=restaurants, session=login_session)

@app.route("/restaurant/new", methods=["GET", "POST"])
def newRestaurant():
    if "username" not in login_session:
        return redirect("/login")

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
    if "username" not in login_session:
        return redirect("/login")

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
    if "username" not in login_session:
        return redirect("/login")

    if request.method == "POST":
        data = request.form

        # check which button is clicked - either DELETE or CANCEL
        if data["action"] == "DELETE":
            r = crud.get_restaurant(r_id)
            crud.delete_restaurant(r_id)
            flash("Restaurant {} Deleted!".format(r.name))

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
    if "username" not in login_session:
        return redirect("/login")

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
    if "username" not in login_session:
        return redirect("/login")

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
    if "username" not in login_session:
        return redirect("/login")

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
    app.run(host="127.0.0.1", port=8000)