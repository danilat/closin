#!/usr/bin/python
# -*- coding: utf-8 -*-
#tiene sentido persistir datos? todo en cliente? y si no soporta base de datos/localStorage?

from google.appengine.ext import db

class Pharmacy(db.Model):
  name = db.StringProperty()
  location = db.GeoPtProperty()
  #teléfono?
class Post(db.Model):
  lines = db.StringListProperty()
  link = db.LinkProperty()
  number = db.	IntegerProperty()
  location = db.GeoPtProperty()
class BiziParking(db.Model):
  name = db.StringProperty()
  location = db.GeoPtProperty()

class Service(db.Model):
	name = db.StringProperty()
	data = db.TextProperty()