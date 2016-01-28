import eventlet
from eventlet.green import socket

PORT = 3001
users = set()

class User(object):
    def __init__(self, connection, address):
        print("Participant joined chat.")
        self.writer = connection.makefile('w')

    def write_line(self, text):
        self.writer.write(text)
        self.writer.flush()

    def left(self):
        print("Participant left chat.")

def message(user, line):
    print("Chat:", line.strip())
    for other in users:
        try:
            if other is not user:  # Don't echo
                other.write_line(line)
        except socket.error as e:
            # ignore broken pipes, they just mean the participant
            # closed its connection already
            if e[0] != 32:
                raise

def handler(user, reader):
    line = reader.readline()
    while line:
        message(user, line)
        line = reader.readline()
    user.left()
    users.remove(writer)

try:
    print("ChatServer starting up on port %s" % PORT)
    server = eventlet.listen(('0.0.0.0', PORT))
    while True:
        connection, address = server.accept()
        user = User(connection, address)
        users.add(user)
        eventlet.spawn_n(handler, user, connection.makefile('r'))
except (KeyboardInterrupt, SystemExit):
    print("ChatServer exiting.")

