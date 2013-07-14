#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

import json

import logging
import urllib
import re
import os
from BeautifulSoup import BeautifulSoup
import model
import xml.dom.minidom

from google.appengine.ext.webapp import template

class BaseHandler(webapp.RequestHandler):
	values = {}
	request = None
	response = None

	def render(self, f):
		self.response.headers['Content-Type'] = 'text/html;charset=UTF-8'
		self.response.headers['Pragma'] = 'no-cache'
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Expires'] = 'Wed, 27 Aug 2008 18:00:00 GMT'
		
		import os
		path = os.path.join(os.path.dirname(__file__), 'templates', f)
		self.response.out.write(template.render(path, self.values))
		
	def render_json(self, data):	
		self.response.headers['Content-Type'] = 'application/json;charset=UTF-8'
		self.response.headers['Pragma'] = 'no-cache'
		self.response.headers['Cache-Control'] = 'no-cache'
		self.response.headers['Expires'] = 'Wed, 27 Aug 2008 18:00:00 GMT'
		self.response.out.write(data)
	
	def create_service(self, name):
		response = urlfetch.fetch('http://api.dndzgz.com/services/'+name).content
		new_api_structure = json.loads(response)
		first_version_structure = new_api_structure['locations']
		for element in first_version_structure:
			element['name'] = element['title']

		service = model.Service.all().filter("name", name).get()
		if not service:
			service = model.Service(name=name, data=json.dumps(first_version_structure))
		else:
			service.data = json.dumps(first_version_structure)
		service.put()
		self.render_json(service.data)
	
	def getaddress(self, lat, lon):
		response = urlfetch.fetch('http://maps.google.com/maps/geo?q='+lat+','+lon).content
		data = json.loads(response)
		#return data['Placemark']['address']
		self.response.out.write(response)
		#self.response.out.write(data['Placemark']['address'])
		
	def findElement(self, nodelist, name):
		for node in nodelist:
			if node.nodeName == name:
				return node
		return None

	def getText(self, nodelist):
		rc = []
		for node in nodelist:
			if node.nodeType == node.TEXT_NODE:
				rc.append(node.data)
		return ''.join(rc)

class WebPage(BaseHandler):
	def get(self):
		self.redirect('/web/index.html')
		
class MainPage(BaseHandler):
	def get(self):
		self.values['categories'] = [
			{'name': 'Autobuses', 'key': 'bus'},
			{'name': 'Bizi', 'key': 'bizi'},
			{'name': 'Tranvía', 'key': 'tram'},
			{'name': 'Farmacias', 'key': 'pharmacies'},
			{'name': 'Parking', 'key': 'parking'},
			{'name': 'Taxis', 'key': 'taxis'},
			{'name': 'Gasolina', 'key': 'gas'},
			{'name': 'WiFi', 'key': 'wizi'},

		]
		self.render('index.html')

class TestPage(BaseHandler):
	def get(self):
		self.render('test.html')

class FetchService(BaseHandler): 
	def get(self):
		name = self.request.get('service')
		service = model.Service.all().filter("name", name).get()
		self.render_json(service.data)

class FecthPharmacy(BaseHandler):
	def get(self):
		self.create_service('pharmacies')

# esto valdrá para posicionar postes, en el json nos devuelve una url donde podemos consultar lo que tardará, mola bastante
# alternativa: scarpping diario de la web de bizi y consultar el estado del parking en tiempo real(petición post)
class FecthBus(BaseHandler):
	def get(self):
		self.create_service('bus')
		
class FecthWifi(BaseHandler):
	def get(self):
		self.create_service('wizi')

class FecthBizi(BaseHandler): 
	def get(self):
		self.create_service('bizi')
		
class FetchTranvia(BaseHandler):
	def get(self):
		self.create_service('tram')
		

class Details(BaseHandler):
	def get(self):
		service = self.request.get('service')
		id = self.request.get('id')
		name = self.request.get('name')
		lat = self.request.get('lat')
		lon = self.request.get('lon')
		slat = self.request.get('slat')
		slon = self.request.get('slon')
		response = ""
		if service =="bus":
			response = urlfetch.fetch('http://www.tuzsa.es/tuzsa_frm_esquemaparadatime.php?poste='+id).content
			soup = BeautifulSoup(response)
			items={}
			rows = soup.table.contents[1].table.findAll('tr')[1:]
			for row in rows:
				linenumber = row.contents[0].string
				row.contents[2].string
				if not items.has_key(linenumber):
					items[linenumber] = {'name': row.contents[1].string, 'buses':[]}
				items[linenumber]['buses'].append(row.contents[2].string)
			address = ''#self.getaddress(lat, lon)
			self.values = {
				'post' : id,
				'address': address,
				'lines' : items,
				'lat': lat,
				'lon':lon,
				'slat' : slat,
				'slon' : slon
			}
			self.render('bus.html')
		elif service == "bizi":
			fields = {
				"addressnew":"RVhQTy4gVE9SUkUgREVMIEFHVUE=",
				"idStation":id,
				"s_id_idioma":"es",
			}
			response = urlfetch.fetch('http://www.bizizaragoza.com/CallWebService/StationBussinesStatus.php',
				urllib.urlencode(fields), urlfetch.POST).content
			soup = BeautifulSoup(response)
			divcontent = soup.div
			name = divcontent.div.contents[0]
			numberofbizis = re.findall('\d+',divcontent.contents[3].contents[0])[0]
			numberofparkings = re.findall('\d+',divcontent.contents[3].contents[2])[0]
			self.values = {
				'name' : id,
				'lat' : lat,
				'lon' : lon,
				'slat' : slat,
				'slon' : slon,
				'numberofbizis' : numberofbizis,
				'numberofparkings': numberofparkings
			}
			self.render('bizi.html')
			
class Point(BaseHandler):
	def get(self):
		service = self.request.get('service')
		id = self.request.get('id')
		name = self.request.get('name')

		items = []
		response = urlfetch.fetch('http://api.dndzgz.com/services/'+service+'/'+id).content
		new_api_structure = json.loads(response)

		if service =="bus":
			if len(new_api_structure['estimates']) > 0:
				for estimate in new_api_structure['estimates']:
					linenumber = estimate['line']
					direction = estimate['direction']
					if estimate['estimate']==0:
						frecuency = 'En la parada'
					else:
						frecuency = str(estimate['estimate']) + ' min'
					items.append([u'[%s] %s' % (linenumber, frecuency), u'Dirección %s' % (direction, )])
			else:
				items.append(['Error obteniendo datos'])
			
			output = {
				'id' : id,
				'service' : service,
				'items' : items,
				'title' : 'Poste %s' % id
			}
		elif service == "bizi":
			fields = {
				"addressnew":"RVhQTy4gVE9SUkUgREVMIEFHVUE=",
				"idStation":id,
				"s_id_idioma":"es",
			}
			response = urlfetch.fetch('http://www.bizizaragoza.com/CallWebService/StationBussinesStatus.php',
				urllib.urlencode(fields), urlfetch.POST).content
			soup = BeautifulSoup(response)
			divcontent = soup.div
			name = divcontent.div.contents[0].strip()
			numberofbizis = re.findall('\d+',divcontent.contents[3].contents[0])[0]
			numberofparkings = re.findall('\d+',divcontent.contents[3].contents[2])[0]
			items = []
			items.append(['%s bicicletas' % numberofbizis])
			items.append(['%s aparcamientos' % numberofparkings])
			output = {
				'id' : id,
				'service' : service,
				'items' : items,
				'title' : name
			}
			
		self.render_json(json.dumps(output))

class Lite(BaseHandler):
	def get(self):
		
		id = self.request.get('id')
		service = self.request.get('service')
		self.values['items'] = None
		if(id != None):
			items = []
			#TODO:refactorizar esto, mogollón de código duplicado de Point
			name=''
			if service =="bus":
				try:
					response = urlfetch.fetch('http://www.tuzsa.es/tuzsa_frm_esquemaparadatime.php?poste='+id).content
					soup = BeautifulSoup(response)
					tables = soup.findAll('table')
					if len(tables) > 1:
						name = 'Poste %s' % id
						table = tables[1]
						rows = table.findAll('tr')[1:]
						for row in rows:
							linenumber = row.contents[0].string
							direction = row.contents[1].string
							frecuency = row.contents[2].string
							frecuency = frecuency.replace('minutos', 'min')
							items.append(u'[%s] %s Dirección %s' % (linenumber, frecuency,direction))
					else:
						items.append(u'Parada sin información')
				except urlfetch.Error, e:
					items.append('Error obteniendo datos')
			elif service == "bizi":
				try:
					fields = {
						"addressnew":"RVhQTy4gVE9SUkUgREVMIEFHVUE=",
						"idStation":id,
						"s_id_idioma":"es",
					}
					response = urlfetch.fetch('http://www.bizizaragoza.com/CallWebService/StationBussinesStatus.php',
					urllib.urlencode(fields), urlfetch.POST).content
					soup = BeautifulSoup(response)
					divcontent = soup.div
					name = 'Parada %s' % id
					#name = divcontent.div.contents[0].strip()
					numberofbizis = re.findall('\d+',divcontent.contents[3].contents[0])[0]
					numberofparkings = re.findall('\d+',divcontent.contents[3].contents[2])[0]
					items.append('%s bicicletas' % numberofbizis)
					items.append('%s aparcamientos' % numberofparkings)
				except:
					items.append('Error obteniendo datos')
					name=''
		self.values['items'] = items
		self.values['name'] = name
		self.render('lite.html')

def main():
  application = webapp.WSGIApplication([('/', WebPage),
										('/app', MainPage),
										('/fetchPharmacy', FecthPharmacy),
										('/fetchBus', FecthBus),
										('/fetchWifi', FecthWifi),
										('/fetchBizi', FecthBizi),
										('/fetchTranvia', FetchTranvia),
										('/details', Details),
										('/point', Point),
										('/fetch', FetchService),
										('/lite', Lite)],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
