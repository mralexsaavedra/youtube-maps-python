import httplib
import json
import os
import urllib
import httplib2
import logging

import jinja2
import webapp2
from webapp2_extras import sessions

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class BaseHandler(webapp2.RequestHandler):
    def dispatch(self):
        self.session_store = sessions.get_store(request=self.request)
        try:
            webapp2.RequestHandler.dispatch(self)
        finally:
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        return self.session_store.get_session()


config = {}
config['webapp2_extras.sessions'] = {'secret_key': 'my-super-secret-key'}


class MainHandler(webapp2.RequestHandler):
    def get(self):
        self.response.write('<a href="/LoginAndAuthorize">Login ant Authorize with Youtube</a>')


class LoginAndAuthorize(BaseHandler):
    def get(self):
        zerbitzaria = 'accounts.google.com'
        conn = httplib.HTTPSConnection(zerbitzaria)
        conn.connect()
        metodoa = 'GET'
        params = {'client_id': '158296640724-bpml9lv2kut0n2n40io4jsuoeg9jm2cs.apps.googleusercontent.com',
                  'redirect_uri': 'http://youtube-api-itocho.appspot.com/callback_uri',
                  'response_type': 'code',
                  'scope': 'https://www.googleapis.com/auth/youtube',
                  'approval_prompt': 'auto',
                  'access_type': 'offline'}
        params_coded = urllib.urlencode(params)
        uri = '/o/oauth2/v2/auth' + '?' + params_coded
        self.redirect('https://' + zerbitzaria + uri)

        logging.debug(params)


class OAuthHandler(BaseHandler):
    def get(self):
        zerbitzaria = 'accounts.google.com'
        metodoa = 'POST'
        uri = '/o/oauth2/token'
        auth_code = self.request.get('code')
        params = {'code': auth_code,
                  'client_id': '158296640724-bpml9lv2kut0n2n40io4jsuoeg9jm2cs.apps.googleusercontent.com',
                  'client_secret': 'hp0SIzs4qRaCvCXbSgdH_0WL',
                  'redirect_uri': 'http://youtube-api-itocho.appspot.com/callback_uri',
                  'grant_type': 'authorization_code'}
        params_encoded = urllib.urlencode(params)
        goiburuak = {'Host': zerbitzaria,
                     'User-Agent': 'Youtube Python bezeroa',
                     'Content-Type': 'application/x-www-form-urlencoded',
                     'Content-Length': str(len(params_encoded))}
        http = httplib2.Http()
        erantzuna, edukia = http.request('https://' + zerbitzaria + uri, method=metodoa, headers=goiburuak,
                                         body=params_encoded)

        jsonEdukia = json.loads(edukia)
        access_token = jsonEdukia['access_token']
        self.session['access_token'] = access_token

        self.redirect('/tokena')


class Youtube(BaseHandler):
    def get(self):
        access_token = self.session.get('access_token')

        zerbitzaria = 'www.googleapis.com'
        metodoa = 'GET'
        uri = '/youtube/v3/channels?part=id&mine=true'
        goiburuak = {'Host': zerbitzaria,
                  'Authorization': 'Bearer ' + access_token,
                  'Content-Type': 'application/octet-stream'}
        http = httplib2.Http()
        erantzuna, edukia = http.request('https://' + zerbitzaria + uri, method=metodoa, headers=goiburuak)

        logging.debug(erantzuna)
        logging.debug(edukia)

        self.redirect('/formularioa')


class FormularioaHartu(BaseHandler):
    def post(self):
        access_token = self.session.get('access_token')
        query = self.request.get('video')
        location = self.request.get('location')
        location_radius = self.request.get('locationRadius')
        zerbitzaria = 'www.googleapis.com'
        uri = '/youtube/v3/search'
        metodoa = 'POST'
        params = {'part': 'snippet',
                  'location': location,
                  'locationRadius': location_radius,
                  'maxResults': 50,
                  'q': query,
                  'type': 'video'}
        params_encoded = urllib.urlencode(params)
        goiburuak = {'Host': zerbitzaria,
                     'Authorization': 'Bearer ' + access_token,
                     'Content-Type': 'application/octet-stream'}
        http = httplib2.Http()
        erantzuna, edukia = http.request('https://' + zerbitzaria + uri + '?' + params_encoded, headers=goiburuak)
        json_erantzuna = json.loads(edukia)
        for each in json_erantzuna['items']:
            video_id = each['id']['videoId']
            self.response.write(video_id+'<br/>')

    def get(self):
        self.redirect('/html/Formulario.html')


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/LoginAndAuthorize', LoginAndAuthorize),
    ('/callback_uri', OAuthHandler),
    ('/tokena', Youtube),
    ('/formularioa', FormularioaHartu)], config=config, debug=True)
