import cgi
import io
import json
import os.path
import webapp2

import simplesite
import starbound

simplesite.TITLE = 'Starbound utilities'
simplesite.MENU = [
    ('Home', '/'),
    ('View data', '/data'),
    ('Repair', '/repair'),
]

def error_with_back(message, path):
    return dict(message=message,
                message_level='danger',
                content='<p><a href="%s">Go back</a></p>' % cgi.escape(path))

class DataHandler(webapp2.RequestHandler):
    @simplesite.page('View data')
    def get(self):
        return (
            '<p>Pick a Starbound file (such as a <code>.world</code> or '
            '<code>.player</code> file) to load it and view its data!</p>'
            '<form action="/data" enctype="multipart/form-data" method="POST">'
            '<p>File to view data for:<br>'
            '<input name="file" type="file"></p>'
            '<p><button class="btn btn-primary" type="submit">View data</button></p>'
            '</form>')

    @simplesite.page('View data')
    def post(self):
        try:
            filename = self.request.POST.get('file').filename
            file = starbound.read_stream(
                io.BytesIO(self.request.get('file')),
                os.path.splitext(filename)[1][1:])
        except Exception as e:
            return error_with_back('Failed to load file: %s' % e.message,
                                   '/data')

        if isinstance(file, starbound.FileSBVJ01):
            raw_data = file.data
        elif isinstance(file, starbound.World):
            raw_data, _ = file.get_metadata()
        else:
            raw_data = 'Could not get any data from that file.'

        data = json.dumps(raw_data,
                          sort_keys=True,
                          indent=2,
                          separators=(',', ': '))

        return (
            '<p>You are viewing a <code>%(identifier)s</code> file of type '
            '<code>%(type)s</code>.</p>'
            '<p>Here is the data section of the file you provided:</p>'
            '<pre>%(data)s</pre>' % dict(identifier=cgi.escape(file.identifier),
                                         type=file.__class__.__name__,
                                         data=cgi.escape(data)))

class HomeHandler(webapp2.RequestHandler):
    @simplesite.page('Home')
    def get(self):
        return (
            '<p>Welcome! This is a very simple utility site for Starbound related '
            'stuff.</p>'
            '<h2>Available actions</h2>'
            '<ul>'
            '<li><a href="/data">View data about a Starbound file</a><br>'
            'For example, a <code>.world</code> or <code>.player</code> file.</li>'
            '<li><a href="/repair">Attempt to restore a broken world</a><br>'
            'Try to repair a world by providing the <code>.fail</code> file.</li>'
            '</ul>')

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
            return error_with_back('Failed to load file: %s' % e.message,
                                   '/repair')

        try:
            world_file = starbound.World(io.BytesIO(self.request.get('world')))
            world_file.initialize()
        except:
            world_file = None

        self.response.write(repr(fail_file.get_metadata()))

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/data', DataHandler),
    ('/repair', RepairHandler),
], debug=True)
