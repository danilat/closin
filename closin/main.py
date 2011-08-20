#!/usr/bin/env python
# -*- coding: utf-8 -*-

from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from django.utils import simplejson as json

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
	
	def create_service(self, name, data):	
		service = model.Service.all().filter("name", name).get()
		if not service:
			service = model.Service(name=name, data=json.dumps(data))
		else:
			service.data = json.dumps(data)
		service.put()
		self.render_json(service.data)
	
	def create_idezar_service(self, name, key, parse_id, create_title, create_subtitle):
		href = '&'.join(['http://idezar2.geoslab.com/URLRelayServlet/URLRelayServlet?urlWFS=http://idezar2.geoslab.com/wfss/wfss',
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
			id = parse_id(data['WFSResponse']['urlList'][i])
			pname = data['WFSResponse']['namesList'][i]
			title = create_title(id, pname)
			result.append({"name": title, "title": title,
				"subtitle": create_subtitle(id, pname),
				"lat": data['WFSResponse']['posYList'][i],
				"lon": data['WFSResponse']['posXList'][i],
				"id": id})
		self.create_service(name, result)
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
			{'name': 'Autobuses', 'key': 'bus', 'zoom': 16},
			{'name': 'Bizi', 'key': 'bizi', 'zoom': 16},
			{'name': 'Tranvía', 'key': 'tranvia', 'zoom': 11},
			{'name': 'WiFi', 'key': 'wifi', 'zoom': 13},
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
		self.create_idezar_service('farmacias', 'Farmacias', lambda s: '', lambda id, name: name, lambda id, name: '')

# esto valdrá para posicionar postes, en el json nos devuelve una url donde podemos consultar lo que tardará, mola bastante
# alternativa: scarpping diario de la web de bizi y consultar el estado del parking en tiempo real(petición post)
class FecthBus(BaseHandler):
	def get(self):
		self.create_idezar_service('bus', 'Transporte%20Urbano', lambda s: s[58:], lambda id, name: 'Poste %s' % (id, ), lambda id, name: u'Líneas: %s' % (name, ))
		
class FecthWifi(BaseHandler):
	def get(self):
		self.create_idezar_service('wifi', 'Zonas%20WIFI', lambda s: s, lambda id, name: name, lambda id, name: '')

class FecthBizi(BaseHandler): 
	def get(self):
		response = urlfetch.fetch('http://www.bizizaragoza.com/localizaciones/station_map.php').content
		self.response.headers['Content-Type'] = 'text/plain'
		response = response.replace('\r', ' ')
		response = response.replace('\n', ' ')
		response = response.replace('\t', ' ')
		#regex = 'GLatLng\((-?\d+\.\d+),(-?\d+\.\d+).+?idStation="\+(\d+)\+\"&addressnew=([a-zA-Z0-9]+)'
		regex = 'GLatLng\((-?\d+\.\d+),(-?\d+\.\d+).+?idStation=(\d+).&addressnew=([a-zA-Z0-9]+)'
		matchobjects = re.finditer(regex, response)
		regex2 = 'idStation="\+(\d+)\+\"&addressnew=([a-zA-Z0-9]+)'
		matchobjects2 = re.finditer(regex2, response)
		print matchobjects2
		result = []
		import base64
		for match in matchobjects:
			s = match.group(4)
			id = match.group(3)
			title = "Parada %s" % (id, )
			
			lendec = len(s) - (len(s) % 4 if len(s) % 4 else 0)
			result.append({"name": title,
				"title": title,
				"subtitle": base64.decodestring(s[:lendec]),
				"lat": float(match.group(1)),
				"lon": float(match.group(2)),
				"id": id})
		
		
		#self.render_json(json.dumps(result))
		self.create_service("bizi", result)
		
class FetchTranvia(BaseHandler):
	def get(self):
		result = []
		response = urlfetch.fetch('http://tranviasdezaragoza.es/xml/main.xml').content
		dom = xml.dom.minidom.parseString(response)
		stops = self.findElement(dom.childNodes[0].childNodes, 'stops')
		for node in stops.childNodes:
			if node.nodeName == 'stop':
				lat = self.getText(self.findElement(node.childNodes, 'Latitude').childNodes)
				lon = self.getText(self.findElement(node.childNodes, 'Longitude').childNodes)
				title = self.getText(self.findElement(node.childNodes, 'name').childNodes)
				result.append({"name": title,
					"title": title,
					"subtitle": "L1",
					"lat": lat,
					"lon": lon,
					"id": ""})
		self.create_service("tranvia", result)
		

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
		if service =="bus":
			items = []
			try:
				response = urlfetch.fetch('http://www.tuzsa.es/tuzsa_frm_esquemaparadatime.php?poste='+id).content
				soup = BeautifulSoup(response)
				tables = soup.findAll('table')
				if len(tables) > 1:
					table = tables[1]
					rows = table.findAll('tr')[1:]
					for row in rows:
						linenumber = row.contents[0].string
						direction = row.contents[1].string
						frecuency = row.contents[2].string
						frecuency = frecuency.replace('minutos', 'min')
						items.append([u'[%s] %s' % (linenumber, frecuency), u'Dirección %s' % (direction, )])
				else:
					items.append([u'Parada sin información'])
			except urlfetch.Error, e:
				items.append(['Error obteniendo datos'])
			output = {
				'id' : id,
				'service' : service,
				'items' : items,
				'title' : 'Poste %s' % id
			}
			self.render_json(json.dumps(output))
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
