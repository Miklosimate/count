import sys
import os

# Ensure the app directory is on the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    # Import the Flask app instance
    from app import app as application
except Exception as e:
    # Fallback WSGI app that shows the import error in the browser
    def application(environ, start_response):
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain; charset=utf-8')])
        msg = "WSGI import error in passenger_wsgi.py:\\n\\n" + repr(e)
        return [msg.encode('utf-8')]