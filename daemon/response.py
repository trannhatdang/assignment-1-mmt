#
# Copyright (C) 2025 pdnguyen of HCMC University of Technology VNU-HCM.
# All rights reserved.
# This file is part of the CO3093/CO3094 course.
#
# WeApRous release
#
# The authors hereby grant to Licensee personal permission to use
# and modify the Licensed Source Code for the sole purpose of studying
# while attending the course
#

"""
daemon.response
~~~~~~~~~~~~~~~~~

This module provides a :class: `Response <Response>` object to manage and persist 
response settings (cookie, auth, proxies), and to construct HTTP responses
based on incoming requests. 

The current version supports MIME type detection, content loading and header formatting
"""
import datetime
import os
import mimetypes
from .authentication import Authentication
from .dictionary import CaseInsensitiveDict

BASE_DIR = ""

class Response():   
    """The :class:`Response <Response>` object, which contains a
    server's response to an HTTP request.

    Instances are generated from a :class:`Request <Request>` object, and
    should not be instantiated manually; doing so may produce undesirable
    effects.

    :class:`Response <Response>` object encapsulates headers, content, 
    status code, cookie, and metadata related to the request-response cycle.
    It is used to construct and serve HTTP responses in a custom web server.

    :attrs status_code (int): HTTP status code (e.g., 200, 404).
    :attrs headers (dict): dictionary of response headers.
    :attrs url (str): url of the response.
    :attrsencoding (str): encoding used for decoding response content.
    :attrs history (list): list of previous Response objects (for redirects).
    :attrs reason (str): textual reason for the status code (e.g., "OK", "Not Found").
    :attrs cookie (CaseInsensitiveDict): response cookie.
    :attrs elapsed (datetime.timedelta): time taken to complete the request.
    :attrs request (PreparedRequest): the original request object.

    Usage::

      >>> import Response
      >>> resp = Response()
      >>> resp.build_response(req)
      >>> resp
      <Response>
    """

    __attrs__ = [
        "_content",
        "_header",
        "status_code",
        "method",
        "headers",
        "url",
        "history",
        "encoding",
        "reason",
        "cookie",
        "elapsed",
        "request",
        "body",
        "reason",
        "auth",
    ]


    def __init__(self, request=None):
        """
        Initializes a new :class:`Response <Response>` object.

        : params request : The originating request object.
        """

        self._content = False
        self._content_consumed = False
        self._next = None

        #: Integer Code of responded HTTP Status, e.g. 404 or 200.
        self.status_code = None

        #: Case-insensitive Dictionary of Response Headers.
        #: For example, ``headers['content-type']`` will return the
        #: value of a ``'Content-Type'`` response header.
        self.headers = {}

        #: URL location of Response.
        self.url = None

        #: Encoding to decode with when accessing response text.
        self.encoding = None

        #: A list of :class:`Response <Response>` objects from
        #: the history of the Request.
        self.history = []

        #: Textual reason of responded HTTP Status, e.g. "Not Found" or "OK".
        self.reason = None

        #: A of cookie the response headers.
        self.cookie = {}

        #: The amount of time elapsed between sending the request
        self.elapsed = datetime.timedelta(0)

        #: The :class:`PreparedRequest <PreparedRequest>` object to which this
        #: is a response.
        self.request = None

        self.auth=""


    def get_mime_type(self, path):
        """
        Determines the MIME type of a file based on its path.

        "params path (str): Path to the file.

        :rtype str: MIME type string (e.g., 'text/html', 'image/png').
        """

        try:
            mime_type, _ = mimetypes.guess_type(path)
        except Exception:
            return 'application/octet-stream'
        return mime_type or 'application/octet-stream'


    def prepare_content_type(self, mime_type='text/html'):
        """
        Prepares the Content-Type header and determines the base directory
        for serving the file based on its MIME type.

        :params mime_type (str): MIME type of the requested resource.

        :rtype str: Base directory path for locating the resource.

        :raises ValueError: If the MIME type is unsupported.
        """

        base_dir = ""

        # Processing mime_type based on main_type and sub_type
        main_type, sub_type = mime_type.split('/', 1)
        # print("[Response] processing MIME main_type={} sub_type={}".format(main_type,sub_type))
        if main_type == 'text':
            self.headers['Content-Type']='text/{}'.format(sub_type)
            if sub_type == 'plain' or sub_type == 'css':
                base_dir = BASE_DIR+"static/"
            elif sub_type == 'html':
                base_dir = BASE_DIR+"www/"
            else:
                # handle_text_other(sub_type) # This function is not defined, raise error
                raise ValueError(f"Unsupported text subtype: {sub_type}")
        elif main_type == 'image':
            base_dir = BASE_DIR+"static/" # Images are in static/ [cite: 213]
            self.headers['Content-Type']='images/{}'.format(sub_type)
        elif main_type == 'application':
            base_dir = BASE_DIR+"apps/"
            self.headers['Content-Type']='application/{}'.format(sub_type)
        #
        #  TODO: process other mime_type
        #        application/xml       
        #        application/zip
        #        ...
        #        text/csv
        #        text/xml
        #        ...
        #        video/mp4 
        #        video/mpeg
        #        ...
        #
        else:
            raise ValueError("Invalid MEME type: main_type={} sub_type={}".format(main_type,sub_type))

        return base_dir


    def build_content(self, path, base_dir):
        """
        Loads the objects file from storage space.

        :params path (str): relative path to the file.
        :params base_dir (str): base directory where the file is located.

        :rtype tuple: (int, bytes) representing content length and content data.
        """

        filepath = os.path.join(base_dir, path.lstrip('/'))
        # print("[Response] serving the object at location {}".format(filepath))

        #
        #  TODO: implement the step of fetch the object file
        #        store in the return value of content
        #

        # --- MODIFICATION ---
        # Authentication logic removed from here and moved to build_response.
        # This function now only loads the file content based on path.
        # --- END MODIFICATION ---

        try:
            if 'images' in filepath or path.endswith('.png') or path.endswith('.jpg'):
                file = open(filepath, "rb")
                content = file.read()
            else:
                # This will correctly open and read login.html, index.html, styles.css, etc.
                file = open(filepath, "r")
                content = file.read().encode('utf-8')
        except FileNotFoundError:
            print(f"[Response] File not found: {filepath}")
            raise Exception("File not found")
        except Exception as e:
            print(f"[Response] Error processing file: {e}")
            raise Exception("Something went wrong processing the file")

        if(content == None):
            raise Exception("Something went wrong processing the file")

        return len(content), content


    def build_response_header(self, request):
        """
        Constructs the HTTP response headers based on the class:`Request <Request>
        and internal attributes.

        :params request (class:`Request <Request>`): incoming request object.

        :rtypes bytes: encoded HTTP response header.
        """
        reqhdr = request.headers
        rsphdr = self.headers

        # print("COOKIES!!!! {}", "; ".join([str(x)+"="+str(y) for x,y in self.cookie.items()]))

        #Build dynamic headers
        headers = {
                "Accept": "{}".format(reqhdr.get("Accept", "application/json")),
                "Accept-Language": "{}".format(reqhdr.get("Accept-Language", "en-US,en;q=0.9")),
                "Authorization": "{}".format(reqhdr.get("Authorization", "Basic <credentials>")),
                "Cache-Control": "no-cache",
                "Content-Type": "{}".format(rsphdr.get('Content-Type', "")),
                "Content-Length": "{}".format(len(self._content)),
                #"Cookie": "{}".format(reqhdr.get("Cookie", "sessionid=xyz789")), #dummy cooki
        #
        # TODO prepare the request authentication
        #
	    # self.auth = ...
                "Set-Cookie": "; ".join([str(x)+"="+str(y) for x,y in self.cookie.items()]), # 
                "Date": "{}".format(datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")),
                "Max-Forward": "10",
                "Pragma": "no-cache",
                "Proxy-Authorization": "Basic dXNlcjpwYXNz",  # example base64
                "Warning": "199 Miscellaneous warning",
                "User-Agent": "{}".format(reqhdr.get("User-Agent", "Chrome/123.0.0.0")),
            }

        # Header text alignment
            #
            #  TODO: implement the header building to create formated
            #        header from the provied headers
            #
        #
        # TODO prepare the request authentication
        #
	# self.auth = ...
        

        fmt_header = ''
        for key in headers:
            # Don't send empty Set-Cookie header
            if key == "Set-Cookie" and not headers[key]:
                continue
            fmt_header += (key + ': ' + headers[key] + '\n')
        fmt_header += '\r\n'
        return fmt_header.encode('utf-8')


    def build_notfound(self):
        """
        Constructs a standard 404 Not Found HTTP response.

        :rtype bytes: Encoded 404 response.
        """

        return (
                "HTTP/1.1 404 Not Found\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 13\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "404 Not Found"
            ).encode('utf-8')


    def build_unauthorized(self):
        # [cite: 352, 356]
        return (
                "HTTP/1.1 401 Unauthorized\r\n"
                "Accept-Ranges: bytes\r\n"
                "Content-Type: text/html\r\n"
                "Content-Length: 16\r\n"
                "Cache-Control: max-age=86000\r\n"
                "Connection: close\r\n"
                "\r\n"
                "401 Unauthorized"
            ).encode('utf-8')
        
    def return_peers(self):
        return "".encode('utf-8')

    def build_response(self, request):
        """
        Builds a full HTTP response including headers and content based on the request.

        :params request (class:`Request <Request>`): incoming request object.

        :rtype bytes: complete HTTP response using prepared headers and content.
        """

        self.request = request

        # If a route handler (WeApRous hook) produced a result, return it directly
        hook_res = getattr(request, 'hook_result', None)
        if hook_res is not None:
            import json as _json

            # Accept either (body, status) or body only
            if isinstance(hook_res, tuple):
                body = hook_res[0]
                status = hook_res[1] if len(hook_res) > 1 else '200 OK'
            else:
                body = hook_res
                status = '200 OK'

            if isinstance(body, (dict, list)):
                body_bytes = _json.dumps(body).encode('utf-8')
                content_type = 'application/json'
            else:
                body_bytes = str(body).encode('utf-8')
                content_type = 'text/plain'

            header = (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(body_bytes)}\r\n"
                "Connection: close\r\n"
                "\r\n"
            ).encode('utf-8')
            return header + body_bytes

        path = request.path
        mime_type = self.get_mime_type(path)
        # print("[Response] {} path {} mime_type {}".format(request.method, request.path, mime_type))

        # --- START MODIFICATION (Task 1A) ---
        # Handle POST /login for authentication 
        if path == '/login' and request.method == 'POST':
            authe = Authentication()
            # Check credentials (e.g., admin/password) [cite: 350]
            if authe.authenticate(self.request.body):
                # Task 1A: Valid credentials
                print("[Response] Authentication successful for /login")
                # Set cookie for header 
                self.cookie["auth"] = 'true'
                
                # Task 1A: Respond with index page 
                path = '/index.html' # Serve index.html
                mime_type = 'text/html'
                
                try:
                    base_dir = self.prepare_content_type(mime_type)
                    c_len, self._content = self.build_content(path, base_dir)
                    self._header = self.build_response_header(request)
                    status = 'HTTP/1.1 200 OK\r\n'.encode('utf-8')
                    return status + self._header + self._content
                except Exception:
                    return self.build_notfound() # If index.html is missing

            else:
                # Task 1A: Invalid credentials, respond with 401 
                print("[Response] Authentication failed for /login")
                return self.build_unauthorized()

        # --- END MODIFICATION ---

        # --- START MODIFICATION (Task 1B) ---
        
        # Handle GET /login (request for the login form itself)
        if path == '/login' and request.method == 'GET':
            path = '/login.html' # Serve login.html from www/
            mime_type = self.get_mime_type(path)
        
        # # Task 1B: Implement cookie-based access control 
        # # Protect all other paths
        # elif not request.auth:
        #     # If cookie is missing or incorrect, respond with 401 [cite: 355, 356]
        #     return self.build_unauthorized()
            
        # --- END MODIFICATION ---

        base_dir = ""

        # Try to prepare content type and get base directory
        try:
            if path.endswith('.html') or mime_type == 'text/html':
                base_dir = self.prepare_content_type(mime_type = 'text/html')
            elif mime_type == 'text/css':
                base_dir = self.prepare_content_type(mime_type = 'text/css')
            elif mime_type == 'image/png':
                base_dir = self.prepare_content_type(mime_type = 'image/png')
            elif mime_type == 'image/jpeg':
                # Added jpg support for welcome.jpg
                base_dir = self.prepare_content_type(mime_type = 'image/jpeg')
            else:
                # Default attempt for other types
                base_dir = self.prepare_content_type(mime_type)
        except ValueError: # Catches unsupported MIME types
            print(f"Unsupported MIME type: {mime_type}")
            return self.build_notfound()
        except Exception as e: # Catch other potential errors
            print(f"Error preparing content type: {e}")
            return self.build_notfound()

        # Try to build the content
        try:
            c_len, self._content = self.build_content(path, base_dir)
        except Exception: # Catch file not found, etc.
            return self.build_notfound()

        self._header = self.build_response_header(request)
        status = 'HTTP/1.1 200 OK\r\n'.encode('utf-8')

        return status + self._header + self._content