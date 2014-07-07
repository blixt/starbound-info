import cgi
import io
import json
import webapp2

import simplesite
import starbound

simplesite.TITLE = 'Starbound utilities'
simplesite.MENU = [
    ('Home', '/'),
    ('Metadata', '/metadata'),
    ('Repair', '/repair'),
]

class HomeHandler(webapp2.RequestHandler):
    @simplesite.page('Home')
    def get(self):
        return (
            '<p>Welcome! This is a very simple utility site for Starbound related '
            'stuff.</p>'
            '<h2>Available actions</h2>'
            '<ul>'
            '<li><a href="/metadata">View metadata about a Starbound file</a><br>'
            'For example, a <code>.world</code> or <code>.player</code> file.</li>'
            '<li><a href="/repair">Attempt to restore a broken world</a><br>'
            'Try to repair a world by providing the <code>.fail</code> file.</li>'
            '</ul>')

class MetadataHandler(webapp2.RequestHandler):
    @simplesite.page('View metadata')
    def get(self):
        return (
            '<p>Pick a Starbound file (such as a <code>.world</code> or '
            '<code>.player</code> file) to load it and view its metadata!</p>'
            '<form action="/metadata" enctype="multipart/form-data" method="POST">'
            '<p>File to view metadata for:<br>'
            '<input name="file" type="file"></p>'
            '<p><button class="btn btn-primary" type="submit">View metadata</button></p>'
            '</form>')

    @simplesite.page('View metadata')
    def post(self):
        try:
            starbound_file = starbound.World(io.BytesIO(self.request.get('file')))
            starbound_file.initialize()
        except Exception as e:
            return dict(message='Failed to load file: %s' % e.message,
                        message_level='danger',
                        content='<p><a href="/metadata">Go back</a></p>')

        data = json.dumps(starbound_file.get_metadata(),
                          sort_keys=True,
                          indent=2,
                          separators=(',', ': '))

        return (
            '<p>Here is the metadata section of the file you provided:</p>'
            '<pre>' + cgi.escape(data) + '</pre>')

class RepairHandler(webapp2.RequestHandler):
    def _form(self):
        return (
            '<p>This tool will attempt to restore your broken world. There is no guarantee '
            'that this will work!</p>'
            '<form action="/repair" enctype="multipart/form-data" method="POST">'
            '<p>Choose a <code>.fail</code> file:<br>'
            '<input name="fail" type="file"></p>'
            '<p>(Optional) Choose the <code>.world</code> file that replaced it:<br>'
            '<input name="world" type="file"></p>'
            '<p><button class="btn btn-primary" type="submit">Attempt repair</button></p>'
            '</form>')

    @simplesite.page('Repair world')
    def get(self):
        return dict(
            message=self.request.get('error'),
            message_level='danger',
            content=self._form())

    def post(self):
        try:
            fail_file = starbound.FailedWorld(io.BytesIO(self.request.get('fail')))
            fail_file.initialize()
        except Exception as e:
            return dict(message='Failed to load file: %s' % e.message,
                        message_level='danger',
                        content='<p><a href="/repair">Go back</a></p>')

        try:
            world_file = starbound.World(io.BytesIO(self.request.get('world')))
            world_file.initialize()
        except:
            world_file = None

        self.response.write(repr(fail_file.get_metadata()))

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/metadata', MetadataHandler),
    ('/repair', RepairHandler),
], debug=True)
