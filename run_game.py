import re
import sys
import artattack.__main__
from artattack.network import DEFAULT_PORT


if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-p', '--painting', help='Painting file to load', default=artattack.__main__.DEFAULT_PAINTING)
    parser.add_option('-t', '--timelimit', help='Time limit for level (0 = unlimited)', default=180, type='int')
    parser.add_option('-s', '--serve', help='Host a network game on port PORT', metavar='PORT', type='int')
    parser.add_option('-c', '--connect', help='Connect to a network game on HOST:PORT', metavar='HOST[:PORT]')

    options, args = parser.parse_args()

    if options.serve and options.connect:
        parser.error("Hosting and connecting are mutually exclusive.")

    if options.serve:
        artattack.__main__.host(options.painting, options.timelimit, port=options.serve)
    elif options.connect:
        mo = re.match('^([\w.-]+)(:(\d+))?', options.connect)
        if not mo:
            parser.error("Invalid format for --connect argument. Should be in host[:port] format.")
        host = mo.group(1)
        port = int(mo.group(3))
        artattack.__main__.connect(host, port)
    else:
        artattack.__main__.main(options.painting, options.timelimit)
