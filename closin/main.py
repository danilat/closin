#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from django.utils import simplejson as json

import urllib
import re
import os
from BeautifulSoup import BeautifulSoup
import model

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
	
	def create_service(self, name, data):	
		service = model.Service.all().filter("name", name).get()
		if not service:
			service = model.Service(name=name, data=json.dumps(data))
		else:
			service.data = json.dumps(data)
		service.put()
		self.render_json(service.data)
	
	def create_idezar_service(self, name, key, parse_id):
		href = '&'.join(['http://155.210.155.158:8080/URLRelayServlet/URLRelayServlet?urlWFS=http://155.210.155.158:8080/wfss/wfss',
			'request=GetFeature',
			'outputformat=text/gml',
			'featureType=PuntosDeInteres',
			'propertyNames=posicion%2Curl%2Cnombre',
			'subtema='+key,
			'srsname=EPSG%3A4326',
			'outputType=3',
			'encodeQuery=true'])
		response = urlfetch.fetch(href).content
		response = response.decode('iso-8859-1').encode('utf-8')
		response = response.replace('\'', '"')
		data = json.loads(response)
		result = []
		for i in range(0, len(data['WFSResponse']['namesList'])):
			result.append({"name": data['WFSResponse']['namesList'][i],
				"lat": data['WFSResponse']['posYList'][i],
				"lon": data['WFSResponse']['posXList'][i],
				"id": parse_id(data['WFSResponse']['urlList'][i])})
		self.create_service(name, result)

class MainPage(BaseHandler):
	def get(self):
		self.values['categories'] = [
			{'name': 'Autobuses', 'key': 'bus', 'zoom': 16},
			{'name': 'Bizi', 'key': 'bizi', 'zoom': 16},
			{'name': 'WiFi', 'key': 'wifi', 'zoom': 13}
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

# sólo posiciona locales :S, farmacias de guardia? teléfono de contacto?
class FecthPharmacy(BaseHandler):
	def get(self):
		self.create_idezar_service('farmacias', 'Farmacias', lambda s: '')

# esto valdrá para posicionar postes, en el json nos devuelve una url donde podemos consultar lo que tardará, mola bastante
# alternativa: scarpping diario de la web de bizi y consultar el estado del parking en tiempo real(petición post)
class FecthBus(BaseHandler):
	def get(self):
		self.create_idezar_service('bus', 'Transporte%20Urbano', lambda s: s[58:])
		
class FecthWifi(BaseHandler):
	def get(self):
		self.create_idezar_service('wifi', 'Zonas%20WIFI', lambda s: s)

# es cosa mía o hay poco que sacar de las bizis aquí? Aparte de posicionar estaciones... nada, ni identificarlas :S
#http://www.bizizaragoza.com/localizaciones/station_map.php parece que será mejor origen de datos
class FecthBizi(BaseHandler): 
	def get(self):
		response = urlfetch.fetch('http://www.bizizaragoza.com/localizaciones/station_map.php').content
		self.response.headers['Content-Type'] = 'text/plain'
		response = response.replace('\r', ' ')
		response = response.replace('\n', ' ')
		response = response.replace('\t', ' ')
		regex = 'GLatLng\((-?\d+\.\d+),(-?\d+\.\d+).+?idStation="\+(\d+)\+\"&addressnew=([a-zA-Z0-9]+)'
		matchobjects = re.finditer(regex, response)
		result = []
		import base64
		for match in matchobjects:
			s = match.group(4)
			result.append({"name": base64.decodestring(s + '=' * (4 - len(s) % 4)),
				"lat": float(match.group(1)),
				"lon": float(match.group(2)),
				"id": match.group(3)})
				
		self.create_service("bizi", result)
  
class Details(BaseHandler):
	def get(self):
		service = self.request.get('service')
		id = self.request.get('id')
		name = self.request.get('name')
		lat = self.request.get('lat')
		lon = self.request.get('lon')
		if service == "bus":
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
			self.values = {
				'post' : id,
				'address': 'C\ Rue del percebe 1',
				'lines' : items
			}
			self.render('bus.html')
		elif service == "bizi":
			fields = {
				"addressnew":"RVhQTy4gVE9SUkUgREVMIEFHVUE=",
				"idStation":id,
				"s_id_idioma":"es",
			}
			response = urlfetch.fetch('http://www.bizizaragoza.com/callwebservice/StationBussinesStatus.php',
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
				'numberofbizis' : numberofbizis,
				'numberofparkings': numberofparkings
			}
			self.render('bizi.html')

def main():
  application = webapp.WSGIApplication([('/', MainPage),
										('/fetchPharmacy', FecthPharmacy),
										('/fetchBus', FecthBus),
										('/fetchWifi', FecthWifi),
										('/fetchBizi', FecthBizi),
										('/details', Details),
										('/fetch', FetchService),
										('/test', TestPage)],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
