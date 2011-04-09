class Signal(object):
    def __init__(self):
        self.handlers = set()

    def connect(self, callback):
        self.handlers.add(callback)

    def disconnect(self, callback):
        self.handlers.remove(callback)

    def fire(self, *args, **kwargs):
        for h in self.handlers:
            h(*args, **kwargs)
