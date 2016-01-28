import eventlet
from eventlet.green import socket

PORT = 3001
participants = set()

def new_user(connection, address):
    print("Participant joined chat.")
    new_writer = new_connection.makefile('w')
    new_writer.write('type your name:')
    new_writer.flush()
    name = new_writer.readline().strip()
    return new_writer

def new_message(writer, line, participants):
    print("Chat:", line.strip())
    for p in participants:
        try:
            if p is not writer:  # Don't echo
                p.write(line)
                p.flush()
        except socket.error as e:
            # ignore broken pipes, they just mean the participant
            # closed its connection already
            if e[0] != 32:
                raise

def read_chat_forever(writer, reader):
    line = reader.readline()
    while line:
        new_message(writer, line, participants)
        line = reader.readline()
    participants.remove(writer)
    print("Participant left chat.")

try:
    print("ChatServer starting up on port %s" % PORT)
    server = eventlet.listen(('0.0.0.0', PORT))
    while True:
        new_connection, address = server.accept()
        new_writer = new_user(new_connection, address)
        participants.add(new_writer)
        eventlet.spawn_n(read_chat_forever,
                         new_writer,
                         new_connection.makefile('r'))
except (KeyboardInterrupt, SystemExit):
    print("ChatServer exiting.")

