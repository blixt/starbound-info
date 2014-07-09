import cgi
import io
import json
import os.path
import random
import re

import cloudstorage as gcs
import webapp2

from google.appengine.api import app_identity

import simplesite
import starbound

simplesite.TITLE = 'Starbound utilities'
simplesite.MENU = [
    ('Home', '/'),
    ('View data', '/data'),
    ('Repair', '/repair'),
]

GCS_BUCKET = '/' + app_identity.get_default_gcs_bucket_name()

def get_gcs_path_for_world(world_id):
    return '%s/%s.world' % (GCS_BUCKET, world_id)

def get_world_filename(world_id):
    return '%s.world' % world_id.split('-')[1]

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
            '<p>Depending on your platform, the Starbound directory will be in different places:</p>'
            '<p><strong>Windows</strong><br>'
            '<code>C:\\Program Files (x86)\\Steam\\SteamApps\\common\\Starbound</code></p>'
            '<p><strong>Mac</strong><br>'
            '<code>/Users/&lt;username&gt;/Library/Application Support/Steam/SteamApps/common/Starbound</code></p>'
            '<form action="/data" enctype="multipart/form-data" method="POST" onsubmit="this.elements.btn.disabled=true">'
            '<p>File to view data for:<br>'
            '<input name="file" type="file"></p>'
            '<p><button class="btn btn-primary" name="btn" type="submit">View data</button></p>'
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

class DownloadHandler(webapp2.RequestHandler):
    def get(self):
        world_id = self.request.get('world')
        filename = get_world_filename(world_id)
        gcs_path = get_gcs_path_for_world(world_id)
        self.response.write('this will be %s from %s' % (filename, gcs_path))

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
            '</ul>'
            '<h2>External links</h2>'
            '<ul>'
            '<li><a href="http://blixt.github.io/starbounded/">Render a world in your browser '
            '<span class="glyphicon glyphicon-new-window"></span></a><br>This will try to render '
            'your world similar to what it looks like in-game.</li>'
            '<li><a href="https://github.com/blixt/py-starbound">Browse Python modules and '
            'command line tools for Starbound <span class="glyphicon glyphicon-new-window">'
            '</span></a><br>GitHub page for the Python tools that power this site and more.</li>'
            '<li><a href="https://github.com/blixt/starbound-info">Browse the source code of this '
            'site <span class="glyphicon glyphicon-new-window"></span></a><br>'
            'The GitHub page for the code that runs this site.</li>'
            '</ul>')

class RepairHandler(webapp2.RequestHandler):
    def _form(self):
        return (
            '<p>This tool will attempt to restore your broken world. There is no guarantee '
            'that this will work!</p>'
            '<p>Your world files can be found in the "universe" directory inside of Starbound\'s '
            'directory. Depending on your platform, it will be in different places:</p>'
            '<p><strong>Windows</strong><br>'
            '<code>C:\\Program Files (x86)\\Steam\\SteamApps\\common\\Starbound</code></p>'
            '<p><strong>Mac</strong><br>'
            '<code>/Users/&lt;username&gt;/Library/Application Support/Steam/SteamApps/common/Starbound</code></p>'
            '<form action="/repair" enctype="multipart/form-data" method="POST" onsubmit="this.elements.btn.disabled=true">'
            '<p>Choose a <code>.fail</code> file<br>'
            '<input name="fail" type="file"></p>'
            '<p>Choose the <code>.world</code> file that replaced it (<em>optional</em>)<br>'
            '<input name="world" type="file"></p>'
            '<p class="text-muted">(The reason for uploading the new world file is so that its '
            'data can be used to patch up the failed world where data is missing. Providing the '
            'fresh file will greatly increase your chances of getting your world back.)</p>'
            '<p><button class="btn btn-primary" name="btn" type="submit">Attempt repair</button></p>'
            '</form>')

    @simplesite.page('Repair world')
    def get(self):
        return self._form()

    @simplesite.page('Repair world')
    def post(self):
        # Attempt to load the failed world.
        try:
            fail_filename = self.request.POST.get('fail').filename
            if not fail_filename.endswith('.fail'):
                raise Exception('File (%s) did not end with ".fail"' % fail_filename)
            fail_file = starbound.FailedWorld(io.BytesIO(self.request.get('fail')))
            fail_file.initialize()
        except Exception as e:
            return error_with_back('Failed to load file: %s' % e.message,
                                   '/repair')

        # Load the "fresh" world to use as a fallback for missing data in the failed world.
        try:
            world_filename = self.request.POST.get('world').filename
            world_file = starbound.World(io.BytesIO(self.request.get('world')))
            world_file.initialize()
        except:
            world_filename = None
            world_file = None

        message_level = None
        message = None

        if world_filename and not fail_filename.startswith(world_filename):
            message_level = 'warning'
            message = ('It looks as if the fail filename (%s) does not start with the provided '
                       'world filename (%s). If the files are for different worlds, you may get '
                       'very strange results!' % (cgi.escape(fail_filename),
                                                  cgi.escape(world_filename)))

        # Create a unique id for the repaired world.
        world_id = '-'.join([
            # Five random hexadecimal characters.
            '%05x' % random.randrange(16**5),
            # Remove potential malicious stuff from filename and limit to 40 characters.
            # (This will be a no-op for original world filenames.)
            re.sub('[^a-z0-9_]+', '', fail_filename.split('.')[0])[:40],
        ])

        # Store the repaired world.
        with gcs.open(get_gcs_path_for_world(world_id), 'w') as f:
            f.write(self.request.get('fail'))

        content = (
            '<p>The repair process has finished. Hopefully your world has been successfully '
            'restored! You can download the world by clicking the link below.</p>'
            '<p><a href="/download?world=%(world_id)s"><span class="glyphicon glyphicon-download">'
            '</span> %(filename)s</a></p>' % dict(world_id=cgi.escape(world_id),
                                                  filename=cgi.escape(get_world_filename(world_id))))

        return dict(content=content, message=message, message_level=message_level)

app = webapp2.WSGIApplication([
    ('/', HomeHandler),
    ('/data', DataHandler),
    ('/download', DownloadHandler),
    ('/repair', RepairHandler),
], debug=True)
