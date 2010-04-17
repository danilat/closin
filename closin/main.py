#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
from google.appengine.api import urlfetch
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util

from django.utils import simplejson as json

import urllib
import re
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

class MainPage(BaseHandler):
	def get(self):
		self.render('index.html')

class FetchService(webapp.RequestHandler): 
	def get(self):
		name = self.request.get('service')
		service = model.Service.all().filter("name", "bus").get()
		self.response.headers['Content-Type'] = 'application/json'
		self.response.out.write(service.data)

# sólo posiciona locales :S, farmacias de guardia? teléfono de contacto?
class FecthPharmacy(webapp.RequestHandler):
  def get(self):
    response = urlfetch.fetch('http://155.210.152.228:8080/URLRelayServlet/URLRelayServlet?urlWFS=http://155.210.152.228:8080/wfss/wfss&request=GetFeature&outputformat=text/gml&featureType=PuntosDeInteres&propertyNames=posicion%2Curl%2Cnombre%2Cicono_grande%2Cicono_medio%2Cicono_peq&subtema=Farmacias&srsname=EPSG%3A4326&outputType=3&encodeQuery=true').content
    self.response.headers['Content-Type'] = 'text/plain'
    self.response.out.write(response)

# esto valdrá para posicionar postes, en el json nos devuelve una url donde podemos consultar lo que tardará, mola bastante
# alternativa: scarpping diario de la web de bizi y consultar el estado del parking en tiempo real(petición post)
class FecthBus(webapp.RequestHandler):
	def get(self):
		response = urlfetch.fetch('http://155.210.155.158:8080/URLRelayServlet/URLRelayServlet?urlWFS=http://155.210.155.158:8080/wfss/wfss&request=GetFeature&outputformat=text/gml&featureType=PuntosDeInteres&propertyNames=posicion%2Curl%2Cnombre%2Cicono_grande%2Cicono_medio%2Cicono_peq&subtema=Transporte%20Urbano&srsname=EPSG%3A4326&outputType=3&encodeQuery=true').content
		self.response.headers['Content-Type'] = 'text/plain'
		response = response.replace('\'', '"')
		data = json.loads(response)
		result = []
		for i in range(0, len(data['WFSResponse']['namesList'])):
			result.append({"name": data['WFSResponse']['namesList'][i],
				"lat": data['WFSResponse']['posYList'][i],
				"lon": data['WFSResponse']['posXList'][i],
				"id": data['WFSResponse']['urlList'][i][58:]})
			# self.response.out.write(name+'\n')
		self.response.out.write(json.dumps(result))
		
		service = model.Service.all().filter("name", "bus").get()
		if not service:
			service = model.Service(name="bus", data=json.dumps(result))
		else:
			service.data = json.dumps(result)
		service.put()

# es cosa mía o hay poco que sacar de las bizis aquí? Aparte de posicionar estaciones... nada, ni identificarlas :S
#http://www.bizizaragoza.com/localizaciones/station_map.php parece que será mejor origen de datos
class FecthBizi(webapp.RequestHandler): 
  def get(self):
   response = urlfetch.fetch('http://155.210.155.158:8080/URLRelayServlet/URLRelayServlet?urlWFS=http://155.210.155.158:8080/wfss/wfss&request=GetFeature&outputformat=text/gml&featureType=PuntosDeInteres&propertyNames=posicion%2Curl%2Cnombre%2Cicono_grande%2Cicono_medio%2Cicono_peq&subtema=Aparcabici%2CBiceberg%2CEstaci%C3%B3n%20Bizi&srsname=EPSG%3A4326&outputType=3&encodeQuery=true').content
   self.response.headers['Content-Type'] = 'text/plain'
   self.response.out.write(response)


class FecthBiziWeb(webapp.RequestHandler): 
  def get(self):
   response = urlfetch.fetch('http://www.bizizaragoza.com/localizaciones/station_map.php').content
   self.response.headers['Content-Type'] = 'text/plain'
   self.response.out.write(response)

#esto devuelve el estado actual de un parking bizi
class Parking(webapp.RequestHandler):
  def get(self):
	fields = {
	       "addressnew":"RVhQTy4gVE9SUkUgREVMIEFHVUE=",
	       "idStation":"1",
	       "s_id_idioma":"es",
	}
	response = urlfetch.fetch('http://www.bizizaragoza.com/callwebservice/StationBussinesStatus.php', urllib.urlencode(fields), urlfetch.POST).content
	self.response.headers['Content-Type'] = 'text/plain'
	soup = BeautifulSoup(response)
	divcontent = soup.div
	name = divcontent.div.contents[0]
	numberofbizis = re.findall('\d+',divcontent.contents[3].contents[0])[0]
	numberofparkings = re.findall('\d+',divcontent.contents[3].contents[2])[0]

	self.response.out.write(divcontent)

#lo que tardarán los autobuses
class Details(webapp.RequestHandler):
	def get(self):
		service = self.request.get('service')
		id = self.request.get('id')
		response = ""
		if service=="bus":
			response = urlfetch.fetch('http://www.tuzsa.es/tuzsa_frm_esquemaparadatime.php?poste='+id).content
			soup = BeautifulSoup(response)
			items={}
			for row in soup.table.contents[1].table.findAll('tr'):
				items[len(items)]=[row.contents[0].string,row.contents[1].string,row.contents[2].string]
			self.response.headers['Content-Type'] = 'text/plain'
			self.response.out.write(items)

def main():
  application = webapp.WSGIApplication([('/', MainPage),
										('/fetchPharmacy', FecthPharmacy),
										('/fetchBus', FecthBus),
										('/fetchBizi', FecthBizi),
										('/fetchBiziWeb', FecthBiziWeb),
										('/details', Details),
										('/parking', Parking),
										('/fetch', FetchService)],
                                       debug=True)
  util.run_wsgi_app(application)


if __name__ == '__main__':
  main()
