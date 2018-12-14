import urllib, json, jinja2, os, webapp2, logging

def pretty(obj):
    return json.dumps(obj, sort_keys=True, indent=2)

GMAPS_KEY = "AIzaSyAPOCmxbx7LbIdEBF7KZQ2ity_o1MeYJyg"
GOOGLE_MAPS_API_URL = 'https://maps.googleapis.com/maps/api/geocode/json'
REFUGE_URL = "https://www.refugerestrooms.org/api/v1/restrooms/by_location.json"


JINJA_ENVIRONMENT = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
                                       extensions=['jinja2.ext.autoescape'],
                                       autoescape=True)


def safeGet(url):
    try:
        return urllib.urlopen(url)
    except urllib.error.HTTPError as e:
        print('The server couln\'t fulfill the request.')
        print('Error code: ', e.code)
    except urllib.error.URLError as e:
        print('We failed to reach a server')
        print('Reason: ', e.reason)
    return None


def getAllLocationData(baseurl=GOOGLE_MAPS_API_URL,
               api_key=GMAPS_KEY,
               address='Cafe On The Ave, Seattle',
               params={},
               ):
    params['key'] = api_key
    params['address'] = address
    url = baseurl + "?" + urllib.urlencode(params)
    data = safeGet(url)
    return convToJson(data)


def getLatLng(dict):
    resultDict = dict["results"]
    lat = resultDict[0]["geometry"]["location"]["lat"]
    lng = resultDict[0]["geometry"]["location"]["lng"]
    return {"lat": lat, "lng": lng}


def convToJson(data):
    return json.loads(data.read())



def getBathroomList(locationData, baseurl=REFUGE_URL, params={}, per_page=50):
    params["lat"] = locationData["lat"]
    params["lng"] = locationData["lng"]
    params["per_page"] = per_page
    url = baseurl + "?" + urllib.urlencode(params)
    response = safeGet(url)
    return convToJson(response)

class Bathroom():
    def __init__(self, bathdict):
        print(bathdict)
        if bathdict["accessible"]:
            self.accessible = bathdict["accessible"]
        else:
            self.accessible = False
        if bathdict["changing_table"]:
            self.babyfriendly = bathdict["changing_table"]
        else:
            self.babyfriendly = False
        if bathdict["unisex"]:
            self.unisex = bathdict["unisex"]
        else:
            self.unisex = False
        if bathdict["distance"]:
            self.distance = str(bathdict["distance"])[:4]
        else:
            self.distance = None
        if bathdict["name"]:
            self.placename = bathdict["name"]
        else:
            self.placename = None
        if bathdict["street"]:
            self.street = bathdict["street"]
        else:
            self.street = None
        if bathdict["state"]:
            self.state = bathdict["state"]
        else:
            self.state = None
        if bathdict["comment"]:
            self.comment = bathdict["comment"]
        else:
            self.comment = None


class MainHandler(webapp2.RequestHandler):
    def get(self):
        logging.info("In MainHandler")
        template_values = {}
        template_values['title'] = "GottaGo!"
        template = JINJA_ENVIRONMENT.get_template('searchbathroom.html')
        self.response.write(template.render(template_values))


class GottaGoSearchResponseHandler(webapp2.RequestHandler):
    def post(self):
        vals = {}
        search_input = self.request.get('search_input')
        accessible = self.request.get('accessible')
        changing_table = self.request.get('changingtable')
        unisex = self.request.get('unisex')
        vals['title'] = "GottaGo!"
        if search_input:
            vals['search_input'] = search_input
            vals['accessible'] = accessible
            locationData = getAllLocationData(address=search_input)
            location = getLatLng(locationData)
            allBathrooms = getBathroomList(locationData=location)
            bathroomresult = [Bathroom(bathroom) for bathroom in allBathrooms]
            bodyTitle = ""
            attributes = []
            if accessible or changing_table or unisex:
                if accessible:
                    attributes.append("Accessible")
                    bodyTitle += "Accessible"
                    bathroomresult = [bathroom for bathroom in bathroomresult if bathroom.accessible]

                if changing_table:
                    attributes.append("Child Friendly")
                    bodyTitle += " Child Friendly"
                    bathroomresult = [bathroom for bathroom in bathroomresult if bathroom.babyfriendly]

                if unisex:
                    attributes.append("Gender Inclusive")
                    bodyTitle += " Gender Inclusive"
                    bathroomresult = [bathroom for bathroom in bathroomresult if bathroom.unisex]
            vals['attributed'] = attributes
            bathroomresult = sorted(bathroomresult, key=lambda x: x.distance)
            vals['bathroomresult'] = bathroomresult
            bodyTitle += " Bathrooms"
            vals['body_title'] = bodyTitle
            template = JINJA_ENVIRONMENT.get_template('bathroomlists.html')
            self.response.write(template.render(vals))
        else:
            template = JINJA_ENVIRONMENT.get_template('searchbathroom.html')
            self.response.write(template.render(vals))


application = webapp2.WSGIApplication([
    ('/bathroomlists', GottaGoSearchResponseHandler),
    ('/.*', MainHandler)
],
    debug=True)