#!/usr/bin/env python3

# CRUD operation on database
# C = Create
# R = Read
# U = Update
# D = Delete

# configuration
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from database_setup import User, Restaurant, MenuItem, Base

class RestaurantCRUD:
    # initialize
    def __init__(self):
        engine = create_engine("postgresql://ravi_:ravi_@localhost:5432/restaurantmenuwithusers")
        Base.metadata.bind = engine
        DBsession = sessionmaker(bind=engine)
        self.session = DBsession()

    # Create
    def create_restaurant(self, name):
        restaurant = Restaurant(name=name)
        self.session.add(restaurant)
        self.session.commit()

    # Read
    def get_all_restaurants(self):
        restaurants = self.session.query(Restaurant).all()
        return restaurants

    def get_restaurant(self, id):
        restaurant = self.session.query(Restaurant).filter_by(id=id).one()
        return restaurant

    # Update
    def update_restaurant_name(self, id, new_name):
        restaurant = self.session.query(Restaurant).filter_by(id=id).one()
        restaurant.name = new_name
        self.session.add(restaurant)
        self.session.commit()

    # Delete
    def delete_restaurant(self, id):
        restaurant = self.session.query(Restaurant).filter_by(id=id).one()
        self.session.delete(restaurant)
        self.session.commit()

    def get_menu_items(self):
        menu_items = self.session.query(MenuItem).all()
        return menu_items

    def get_rest_menu_items(self, r_id):
        r_menu_items = self.session.query(MenuItem).filter_by(restaurant_id=r_id).all()
        return r_menu_items

    def get_menu_item(self, r_id, m_id):
        menu_item = self.session.query(MenuItem).filter_by(restaurant_id=r_id, id=m_id).one()
        return menu_item

    def update_menu_item(self, r_id, m_id, new_name='', new_course='', new_desc='', new_price=''):
        menu_item = self.session.query(MenuItem).filter_by(restaurant_id=r_id, id=m_id).one()
        if new_name:
            menu_item.name = new_name
        if new_desc:
            menu_item.description = new_desc
        if new_price:
            menu_item.price = new_price
        if new_course:
            menu_item.course = new_course
        return menu_item

    def delete_menu_item(self, r_id, m_id):
        menu_item = self.session.query(MenuItem).filter_by(restaurant_id=r_id, id=m_id).one()
        self.session.delete(menu_item)
        self.session.commit()

    def create_menu_item(self, r_id, name, description, course, price):
        menu_item = MenuItem()
        menu_item.name = name
        menu_item.description = description
        menu_item.course = course
        menu_item.price = price
        menu_item.restaurant = self.session.query(Restaurant).filter_by(id=r_id).one()
        self.session.add(menu_item)
        self.session.commit()

    def createUser(self, login_session):
        newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
        self.session.add(newUser)
        self.session.commit()
        user = self.session.query(User).filter_by(email=login_session['email']).one()
        return user.id


    def getUserInfo(self, user_id):
        user = self.session.query(User).filter_by(id=user_id).one()
        return user


    def getUserID(self, email):
        try:
            user = self.session.query(User).filter_by(email=email).one()
            return user.id
        except:
            return None

