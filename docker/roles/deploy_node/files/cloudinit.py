#!/usr/bin/python
""" Simple HTTP Server """

import sys
import BaseHTTPServer

class MyHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """ Simple HTTP Handler """
    def do_GET(self):
        """ Respond to a GET Request """

        address, _ = self.client_address

        data = None

        if self.path == '/user-data':
            data = get_file(address, 'user-data')
        elif self.path == '/meta-data':
            data = get_file(address, 'meta-data')

        if data != None:
            self.send_response(200)
        else:
            self.send_response(404)
            data = "File not found"

        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(data)
        return


def get_file(address, config):
    """ Get the config file"""
    path = 'config/' + address + '/' + config
    try:
        with open(path, 'r') as content_file:
            content = content_file.read()
    except IOError:
        return None
    return content

def serve():
    """ Start Server """

    handler_class = MyHandler
    server_class = BaseHTTPServer.HTTPServer

    if sys.argv[1:]:
        port = int(sys.argv[1])
    else:
        port = 8765 
    server_address = ('0.0.0.0', port)

    httpd = server_class(server_address, handler_class)

    sock = httpd.socket.getsockname()
    print "Serving HTTP on", sock[0], "port", sock[1], "..."
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    serve()

