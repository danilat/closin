#tiene sentido persistir datos? todo en cliente? y si no soporta base de datos/localStorage?

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