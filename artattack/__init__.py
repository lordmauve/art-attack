# Version number - this allows users to see who has the more out-of-date version
VERSION = (1, 0, 4)

# An automatically substituted revision ID; this ensures users are on identical revisions
REVISION = '$Revision$'

# A string representation of the version
VERSION_STRING = '.'.join([str(v) for v in VERSION])

if __name__ == "__main__":
    import main
    main.main()
