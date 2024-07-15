import socket
import re
import os

class HTTP_ResponsePage :
    def __init__(self) -> None:
        self.notfoundPage = b'404 page not found'
        self.badRequest = b'400 bad request'
        self.versionError = b'505 HTTP Version Not Supported'
        self.unauthiruzed = b'401 Unauthorized'
        self.updatePage = b'the page is update'
        self.deletePage = b'file is deleted'

class HTTP_StatusCode :
    def __init__(self) -> None:
        self.status200 = b'200 OK'
        self.status301 = b'301 Moved Permanently'
        self.status400 = b'400 Bad Request'
        self.status401 = b'401 Unauthorized'
        self.status404 = b'404 Not Found'
        self.status505 = b'505 HTTP Version Not Supported'
    

class HTTP_Response :
    def __init__(self) -> None:
        self.statusCode = HTTP_StatusCode()
        self.responsePage = HTTP_ResponsePage()
        self.status = 200
        self.response_header = b''
        self.response_body = b''

    def create_response_body( self, method, path ) :
        self.response_body = b''
        if self.status == 404 :
            self.response_body += self.responsePage.notfoundPage
        elif self.status == 400 :
            self.response_body += self.responsePage.badRequest
        elif self.status == 505 :
            self.response_body += self.responsePage.versionError
        elif self.status == 200 :
            if method == b'DELETE' :
                self.response_body += self.responsePage.deletePage
            else :
                with open( path, "rb" ) as file :
                    self.response_body = file.read()
                    file.close()

    def create_method_response_header( self, path )->None :
        self.response_header = b'HTTP/1.1 ' + self.statusCode.status200 + b'\r\n'
        self.response_header += b'Content-Length: ' + str( os.path.getsize( path ) ).encode() + b'\r\n'
        self.response_header += b'Content-Type: text/plain' + b'\r\n'

    def write_data_to_file( self, path, body )->None :
        with open( path, "w+b" ) as file :
            file.write(body)
            file.close()

    def create_response_header( self, version, method, path, body )->None :
        self.response_header = b''
        if version != b'HTTP/1.1' :
            self.status = 505
            self.response_header += b'HTTP/1.1 ' + self.statusCode.status505 + b'\r\n'
            self.response_header += b'Content-Length: ' + str( len(self.responsePage.badRequest ) ).encode() + b'\r\n'
            self.response_header += b'Content-Type: text/plain' + b'\r\n'
            return
        
        if method != b'GET' and method != b'POST' and method != b'DELETE' and method != b'PUT' and method != b'HEAD' :
            self.status = 400
            self.response_header += b'HTTP/1.1 ' + self.statusCode.status400 + b'\r\n'
            self.response_header += b'Content-Length: ' + str( len(self.responsePage.badRequest ) ).encode() + b'\r\n'
            self.response_header += b'Content-Type: text/plain' + b'\r\n'
            return

        if path == b'login' :
            self.status = 301
            self.response_header += b'HTTP/1.1 ' + self.statusCode.status301 + b'\r\n'
            self.response_header += b'Set-Cookie: auth=true' + b'\r\n'
            self.response_header += b'Location: /index.txt' + b'\r\n'
            return

        if path == b'old_page' :
            self.status = 301
            self.response_header += b'HTTP/1.1 ' + self.statusCode.status301 + b'\r\n'
            self.response_header += b'Location: /index.txt' + b'\r\n'
            return

        if method != b'POST' :
            if not os.path.isfile( path ) :
                self.status = 404
                self.response_header = b'HTTP/1.1 ' + self.statusCode.status404 + b'\r\n'
                self.response_header += b'Content-Length: ' + str( len(self.responsePage.notfoundPage ) ).encode() + b'\r\n'
                self.response_header += b'Content-Type: text/plain' + b'\r\n'
            else :
                self.status = 200
                if method == b'GET' or method == b'HEAD' :
                    self.create_method_response_header( path )
                if method == b'PUT' :
                    self.write_data_to_file( path, body )
                    self.create_method_response_header( path )
                if method == b'DELETE' :
                    os.remove( path )
                    self.response_header = b'HTTP/1.1 ' + self.statusCode.status200 + b'\r\n'
                    self.response_header += b'Content-Length: ' + str( len(self.responsePage.deletePage ) ).encode() + b'\r\n'
                    self.response_header += b'Content-Type: text/plain' + b'\r\n'
            return 
        
        else :
            self.write_data_to_file( path, body )
            self.create_method_response_header( path )
                     
    def unauth_response( self )->bytes :
        self.response_header = b''
        self.response_body = b''
        self.response_header = b'HTTP/1.1 ' + self.statusCode.status401 + b'\r\n'
        self.response_header += b'Content-Length: ' + str( len(self.responsePage.unauthiruzed ) ).encode() + b'\r\n'
        self.response_header += b'Content-Type: text/plain' + b'\r\n'
        self.response_body += self.responsePage.unauthiruzed
        return self.response_header + b'\r\n' + self.response_body

    def create_response( self, version, method, path, body, status=200 )->bytes :
        self.response_header = b''
        self.response_body = b''
        self.create_response_header( version, method, path, body )
        if method != b'HEAD' :
            self.create_response_body( method, path )
        return self.response_header + b'\r\n' + self.response_body


class HTTPHeader:
    def __init__(self) ->None :
        self.method = b''
        self.path = b''
        self.version = b''
        self.content_type = ''
        self.content_length = 0
        self.cookies = b''
    
    def get_content_length(self, header:bytes ) :
        pattern = re.compile(b'content-length', re.IGNORECASE)
        match = pattern.search(header)
        if match :
            match = re.search(r'(\d+)$', header.decode())
            self.content_length = int(match.group(1))

    def get_content_type( self, header:bytes ) :
        pattern = re.compile(b'content-type', re.IGNORECASE)
        match = pattern.search(header)
        if match :
            match = re.search(r':\s*(.*)', header.decode())
            self.content_type = match.group(1).strip()

    def get_content_Cookie( self, header:bytes ) :
        pattern = re.compile(b'Cookie', re.IGNORECASE)
        match = pattern.search(header)
        if match :
            match = re.search(r':\s*(.*)', header.decode())
            self.cookies = match.group(1).strip()

    def get_request( self, header:bytes ) :
        request_list = header.split(b' ')
        self.method = request_list[0]
        self.path = request_list[1]
        self.path = self.path[1:]
        self.version = request_list[2]

class WebServer :
    def __init__(self, ip_address:str, port:int) -> None:
        self.header = HTTPHeader()
        self.http_response = HTTP_Response()
        self.body = b''
        self.ip_address = ip_address
        self.port = port
        self.conn = None
        self.addr = None
        self.server = None
        self.header_list = list()
        if self.server == None :
            self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def create_server(self) ->None:
        self.server.bind( (self.ip_address, self.port) )
        self.server.listen(5)
    
    def wait_for_client_connect(self) ->socket:
        self.conn, self.addr = self.server.accept()
        return self.conn

    def send_data_to_client(self, response) ->None:
        self.conn.send( response )

    def read_header_from_client(self) ->bytes:
        pre_white_space = False
        self.header_list = list()
        header = b''
        
        while True :
            byte_data = self.conn.recv( 1 )
            if byte_data == b'\r' :
                byte_data = self.conn.recv( 1 )
                if byte_data == b'\n'  :
                    if pre_white_space == True :
                        break
                    else : pre_white_space = True

                self.header_list.append( header )
                header = b''
                continue
            else : 
                pre_white_space = False
            header += byte_data
        
        return self.header_list 

    def close( self )->None :
        self.conn.close()

    def read_body_from_client(self) ->bytes:
        self.body = b''
        for _ in range(self.header.content_length) :
            byte_data = self.conn.recv( 1 )
            self.body += byte_data
        return self.body

    def paser_header(self) ->None:
        index = 0 
        for header in self.header_list :
            if index == 0 :
                self.header.get_request( header )
            else :
                self.header.get_content_length( header )
                self.header.get_content_type( header )
                self.header.get_content_Cookie( header )
            index += 1

    def process_http_request( self )->bytes:
        if self.header.cookies == b'' and self.header.path != b'login' :
            return self.http_response.unauth_response()
        return self.http_response.create_response( self.header.version, self.header.method, self.header.path, self.body )
            

    def run( self ) ->None:
        self.create_server()
        while True :
            print('wait for client connect.......')
            self.wait_for_client_connect()
            print( 'connected!' )

            self.read_header_from_client()
            self.paser_header()
            print( self.header.cookies )
            self.read_body_from_client()
            response = self.process_http_request()
            print( response )
            self.send_data_to_client( response )
            print( 'close the connect ! ' )


if __name__ == '__main__' :
    server = WebServer('140.135.11.176', 9100)
    server.run()

