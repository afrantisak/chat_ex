import eventlet
from eventlet.green import socket

users = set()

class User(object):
    def __init__(self, connection, address):
        print("Participant joined chat.")
        self.writer = connection.makefile('w')
        self.reader = connection.makefile('r')

    def write(self, text):
        self.writer.write(text)
        self.writer.flush()

    def read(self):
        return self.reader.readline()

    def left(self):
        print("Participant left chat.")

def broadcast(message, from_user):
    print("Chat:", message.strip())
    for user in users:
        try:
            if user is not from_user:  # Don't echo
                user.write(message)
        except socket.error as e:
            # ignore broken pipes, they just mean the participant
            # closed its connection already
            if e[0] != 32:
                raise

def handle(user):
    message = user.read()
    while message:
        broadcast(message, user)
        message = user.read()
    user.left()
    users.remove(writer)

def server(port):
    try:
        print("ChatServer starting up on port %s" % port)
        server = eventlet.listen(('0.0.0.0', port))
        while True:
            connection, address = server.accept()
            user = User(connection, address)
            users.add(user)
            eventlet.spawn_n(handle, user)
        return 0
    except (KeyboardInterrupt, SystemExit):
        print("ChatServer exiting.")
        return 1

def main():
    return server(3001)

if __name__ == '__main__':
    import sys
    sys.exit(main())
