import eventlet
from eventlet.green import socket

def stream(readable):
    data = readable.read()
    while data:
        yield data
        data = readable.read()
    
class User(object):
    def __init__(self, connection, address):
        self.connection = connection
        self.address = address
        self.writer = connection.makefile('w')
        self.reader = connection.makefile('r')
        self.name = self.get_name()

    def get_name(self):
        self.write("Enter your name: ")
        return self.read().strip()

    def write(self, text):
        self.writer.write(text)
        self.writer.flush()

    def read(self):
        return self.reader.readline()

users = set()
    
def broadcast(message, from_user):
    print(from_user.name + ":" + message.strip())
    for user in users:
        try:
            if user is not from_user:  # Don't echo
                user.write(from_user.name + ": " + message)
        except socket.error as e:
            # ignore broken pipes, they just mean the participant
            # closed its connection already
            if e[0] != 32:
                raise
            
def handle(user):
    print("Participant joined chat.")
    users.add(user)
    for message in stream(user):
        broadcast(message, user)
    users.remove(writer)
    print("Participant left chat.")

def service(port):
    try:
        print("ChatServer starting up on port %s" % port)
        server = eventlet.listen(('0.0.0.0', port))
        while True:
            connection, address = server.accept()
            user = User(connection, address)
            eventlet.spawn_n(handle, user)
        return 0
    except (KeyboardInterrupt, SystemExit):
        print("ChatServer exiting.")
        return 1

def main():
    return service(3001)

if __name__ == '__main__':
    import sys
    sys.exit(main())
