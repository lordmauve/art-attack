import sys
import artattack.__main__
if __name__ == "__main__":
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-p', '--painting', help='Painting file to load', default=artattack.__main__.DEFAULT_PAINTING)
    parser.add_option('-t', '--timelimit', help='Time limit for level (0 = unlimited)', default=120, type='int')
    options, args = parser.parse_args()
    artattack.__main__.main(options.painting, options.timelimit)
