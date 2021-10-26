import argparse
import os.path
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import logging
from collections import Counter

class Config:

    DEFAULT_ROOT = '.'
    STATIC_ROOT = DEFAULT_ROOT
    VERSION = '1.0'
    CMD_ARGS = ['?']

def gcd(a, b):
    q = a % b
    return b if q == 0 else gcd(b, q)

class FormData:

    def __init__(self, body):
        self._data = parse_qs(body.decode())

    def single(self, key):
        if key in self._data:
            value = self._data[key][0].strip() 
            return value if value else None
        else:
            return None

    def __str__(self):
        return str(self._data) 


class S(BaseHTTPRequestHandler):
    def _set_headers(self, status=200):
        self.send_response(status)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def _error(self, status):
        self.send_response(status)
        self.end_headers()

    def _html(self, clazz, message):
        """This just generates an HTML document that includes `message`
        in the body. Override, or re-write this do do more interesting stuff.
        """

        style = """
            .echo-requestline {
                display: grid;
                grid-template-columns: 20% 80%;
                background: #1d65a6;
                color: #FFFFFF;
                font-family: 'SanSerif', Arial, sans-serif;
                line-height: 1.2em;
                text-indent: 30px;
                border-radius: 30px;
                font-size: 1.5em;
            }

            .echo-bottom {
                margin-top: 30px;
                display: grid;
                grid-template-columns: 50% 50%;
            }

            .echo-left {
                 margin-right: 5px;
            }

           .echo-panel {
                display: grid;
                grid-template-rows: 50px;
            }

            .echo-table-title {
                text-align: center;
                background: #2e75a6;
                color: #FFF0F0;
                padding: 10px;
            }

            .echo-table {
                display: grid;
                grid-template-columns: 50% 50%;
            }

            .echo-table-left {
                 background: #2e75c8;
                 color: #FFF0F0;
                 padding: 5px;
                 margin-bottom: 2px;
             }

             .echo-table-right {
                 background: #2e53c8;
                 color: #FFF0F0;
                 padding: 5px;
                 margin-bottom: 2px;
             }



            .config-panel {
                display: grid;
                grid-template-columns: 50% 50%;
            }

            .panel {
              width: 90%;
              margin: 0 auto;
              background: #1d65a6;
              color: #00043F;
              font-family: 'SanSerif', Arial, sans-serif;
              line-height: 1.2em;
              text-indent: 30px;
              border-radius: 30px;
            }

            .cell {
                padding: 5px;
            }

            .pd {
                font-family: 'SanSerif', Arial, sans-serif;
                font-size: 1.5em;
            }

            .cfg-key {
                background: #72a2c0;
                overflow: hidden;
                position: relative;
            }
            .file {
                background: #192e5b;
                color: #cccccc;
                font-family: 'Lucida Sans', Arial, sans-serif;
                font-size: 1.2em; line-height: 1.5em;
                text-indent: 30px; margin: 0;
                text-align: center;
                border-radius: 30px;
                margin: 30px;
                padding: 10px;
            }
            a {
                color: #cccccc;
            }
            .index_body {
                background: #f2a104;
                display: grid;
                grid-template-columns: 60% 40%;
            }

            .echo_body {
                background: #f2a104;
            }

            .centered {
                text-align: center;
            }
        """
        content = f"""
        <html>
            <head>
                <style type="text/css">
                    {style}
                </style>
            </head>
            <body class="{clazz}">
                {message}
            </body>
        </html>
        """
        return content.encode("utf8")  # NOTE: must return a bytes object!

    def do_GET(self):
        logging.info('Got GET request: ' + self.path)

        if self.path == '/':
            self.do_base()
            return
        elif self.path == '/echo' or self.path.startswith('/echo?'):
            self.do_echo()
            return

        try:
            fname = os.path.join(Config.STATIC_ROOT, self.path[1:])
            logging.info(f'try to read {fname}')
            with open(fname) as f:
                text = f.read()
            logging.info(f'read {len(text)} chars')
            logging.info(text)
            self._set_headers()
            self.wfile.write(text.encode("utf8"))
        except FileNotFoundError:
            logging.info(f'not found file: {self.path}, '
                    f'locally known as {fname}')
            self._set_headers(404)
            self.wfile.write(Templates.not_found(self.path).encode("utf8"))
        except Exception as e:
            logging.info(f'something is wrong: {e}')
            self._set_headers(500)
            self.wfile.write(Templates.error(self.path, e).encode("utf8"))


    def do_HEAD(self):
        self._set_headers()

    def do_POST(self):
        if self.path == '/echo' or self.path.startswith('/echo?'):
            self.do_echo()
        elif self.path.startswith('/forward'):
            self.do_forward()
        elif self.path.startswith('/textstat'):
            self.do_textstat()
        elif self.path.startswith('/text'):
            self.do_text()
        elif self.path.startswith('/fontanka'):
            self.do_fontanka()
        elif self.path.startswith('/gcd'):
            self.do_gcd()
        elif self.path.startswith('/app/blog'):
            pass 
        else:
            self.wfile.write(self._html("qqq", "POST!"))

    def do_base(self):
        self._set_headers()
        self.wfile.write(self._html("index_body", Templates.base()))

    def do_echo(self):
        self._set_headers()
        self.wfile.write(self._html("echo_body", Templates.echo(self)))

    def do_forward(self):
        fields = FormData(self.get_body())
        where = fields.single("url")

        if where is None:
            self._set_headers()
            self.wfile.write(self._html("error", Templates.form_error('No URL. Sorry')))
            return

        if not where.startswith('https://') and not where.startswith('http://'):
            where = 'https://' + where

        self.send_response(301)
        self.send_header('Location', where)
        self.end_headers()

    def do_fontanka(self):
        fields = FormData(self.get_body())
        when = fields.single("date")

        if when is None:
            self._set_headers()
            self.wfile.write(self._html("error", Templates.form_error('No date. Sorry')))
            return

        yyyy, mm, dd = map(int, when.split('-'))
        self.send_response(301)
        self.send_header('Location', f'https://fontanka.ru/{yyyy:04d}/{mm:02d}/{dd:02d}/all.html')
        self.end_headers()

    def do_gcd(self):
        fields = FormData(self.get_body())
        a = fields.single("a")
        b = fields.single("b")

        if a is None or b is None:
            self._set_headers()
            self.wfile.write(self._html("error", Templates.form_error('No values. Sorry')))
            return

        a, b = map(int, (a, b))
        self._set_headers()
        self.wfile.write(self._html("gcd", Templates.gcd(a, b, gcd(a, b))))

    def do_textstat(self):
        fields = FormData(self.get_body())
        text = fields.single("text")

        if text is None:
            self._set_headers()
            self.wfile.write(self._html("error", Templates.form_error('No text. Sorry')))
            return

        self._set_headers()
        stat = Counter(c for c in text.lower() if c in 'abcdefghijklmnopqrstuvwxyz')
        self.wfile.write(self._html("textstat", Templates.textstat(stat)))

    def do_text(self):
        field_data = self.get_body()
        fields = parse_qs(field_data)
        print(fields)
        redirect = fields.get('redirect', [''])[0].strip()
        link = fields.get('link', [''])[0].strip()
        if redirect:
            self.send_response(301)
            self.send_header('Location', redirect)
            self.end_headers()
            return

        tail = ''
        if link:
            tail = f'<p>Go <a href={link}>here</a></p>'

        self._set_headers()
        if fields.get('comment', [''])[0].strip():
            self.wfile.write(self._html("text_body", f'<h2 style="bqackground: light-blue;">Thank you for comment</h2> {tail}'))
        else:
            self.wfile.write(self._html("text_body", f'<h2>No comment :(</h2> {tail}'))

    def get_body(self):
        length = int(self.headers['content-length'])
        return self.rfile.read(length)


def run(server_class=HTTPServer, handler_class=S, addr="localhost", port=8000, static_root='.'):
    server_address = (addr, port)
    print(server_address)
    httpd = server_class(server_address, handler_class)

    print(f"Starting httpd server on {addr}:{port}")
    httpd.serve_forever()


class Templates:

    @staticmethod
    def not_found(name):
        return f'''
            <p>Not found {name} (local name: {os.path.join(Config.STATIC_ROOT, name[1:])})</p>
        '''

    def error(name, e):
        return f'''
            <p>Error on server size: {e} (local name: {os.path.join(Config.STATIC_ROOT, name[1:])})</p>
        '''

    @staticmethod
    def form_error(description):
        return f'<p>{description}</p>' 

    @staticmethod
    def gcd(a, b, g):
        return f'<p style="font-size: 3em;">GCF({a}, {b}) is <em>{g}</em></p>'

    @staticmethod
    def textstat(stat):
        return f'<table style="font-size: 3em;" width="100%">' + \
               ''.join(f'<tr><td width="50%" style="background: #33DD33;">{k}</td><td width="50%" style="background: lightblue;">{v}</td></tr>' for k, v in stat.most_common()) + \
               '</table>'

    @staticmethod
    def echo(request):
        header_divs = ''.join(f'<div class="echo-table-left">{k}</div> <div class="echo-table-right">{v}</div>' for k, v in request.headers.items())
        length = int(request.headers.get('content-length'))
        data = request.rfile.read(length).decode()
        fields = parse_qs(data)
        data_divs = f'<div class="echo-table-left">Body</div> <div class="echo-table-right">{data}</div>'
        data_divs += ''.join(f'<div class="echo-table-left">{k}</div> <div class="echo-table-right">{v[0] if len(v) == 1 else v}</div>' for k, v in fields.items())
        return f'''
        <div class="echo-panel">
            <div class="echo-requestline cell">
                <div>Request line</div>
                <div>{request.requestline}</div>
            </div>

            <div class="echo-bottom">
                <div class="echo-left">
                    <div class="echo-headers">
                        <div class="echo-table-title">Headers</div>
                        <div class="echo-table">
                            {header_divs}
                        </div>
                    </div>
                </div>

                <div class="echo-right">
                    <div class="echo-headers">
                        <div class="echo-table-title">Data</div>
                        <div class="echo-table">
                            {data_divs}
                        </div>
                    </div>
                </div>
            </div>
        </div>
        '''

    @staticmethod
    def base():
        files = sorted(f for f in os.listdir() if os.path.isfile(f) and (f.endswith('.html') or f.endswith('.htm') ))
        if files:
            f_rows = '\n'.join(f'''
                    <a href=/{f}><div class="file"> {f} </div> </a>
                ''' for f in files)
        else:
            f_rows = '<div style="text-align: center; background: red; padding: 10px; border-radius: 30px;">No files found</div>'

        return f'''
        <div class="pd">
            <h2 style="text-align: center; width: 90%;">Configuration</h2>
            <div class="config-panel panel">
                <div class="cfg-key cell" style="border-top-left-radius: 30px;">Static root</div>
                <div class="cell">{Config.STATIC_ROOT}</div>

                <div class="cfg-key cell">Version</div>
                <div class="cell">{Config.VERSION}</div>

                <div class="cfg-key cell">Working dir</div>
                <div class="cell">{os.getcwd()}</div>

                <div class="cfg-key cell" style="border-bottom-left-radius: 30px;">Log file</div>
                <div class="cell">{os.path.join(Config.STATIC_ROOT, 'server.log')}</div>

            </div>
        </div>


        <div class="pd">
            <h2 style="text-align: center; width: 90%;">HTML files</h2>
            {f_rows}
        </div>
    '''

def main():
    Config.CMD_ARGS = sys.argv[:]
    parser = argparse.ArgumentParser(description="Run a simple HTTP server")
    parser.add_argument(
        "-l",
        "--listen",
        default="localhost",
        help="Specify the IP address on which the server listens",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Specify the port on which the server listens",
    )
    parser.add_argument(
        "-s",
        "--static-root",
        type=str,
        default=Config.DEFAULT_ROOT,
        help="Specify the root of static files",
    )

    args = parser.parse_args()
    Config.STATIC_ROOT = os.path.abspath(args.static_root)

    logging.basicConfig(filename=os.path.join(Config.STATIC_ROOT, 'server.log'), level=logging.DEBUG,
            format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')

    run(addr=args.listen, port=args.port)


if __name__ == "__main__":
    main()

