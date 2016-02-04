import os
import sys
import time
import Queue
import signal
import subprocess
import threading
import contextlib

class Subprocess(object):
    def __init__(self, command_line, shell=False, debug_stdout=False):
        self.command_line = command_line
        self.shell = shell
        self.debug_stdout = debug_stdout
        self.thread = threading.Thread(target=self._run)
        self.process = None
        self.queue = Queue.Queue()
        self.stdout = ''

    def start(self):
        self.thread.start()

    def kill(self):
        if self.process:
            os.killpg(os.getpgid(self.process.pid), signal.SIGKILL)
        self.thread.join()
        
    def _run(self):
        self.process = subprocess.Popen(self.command_line,
                                        stdout=subprocess.PIPE,
                                        shell=self.shell,
                                        preexec_fn=os.setsid)
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            if self.debug_stdout:
                print "Subprocess:", line.rstrip()    
            self.queue.put(line)
        while not self.queue.empty():
            self.stdout += self.queue.get()

    def wait_line(self):
        while self.queue.empty():
            time.sleep(0.1)
        return self.queue.get().strip()
        
class PythonSubprocess(Subprocess):
    def __init__(self, script_path, debug_stdout=False):
        python = sys.executable
        command_line = '{python} -u {script_path}'.format(**locals()).split()
        super(PythonSubprocess, self).__init__(command_line, debug_stdout=debug_stdout)

@contextlib.contextmanager
def AutoPythonSubprocess(script_path, debug_stdout=False):
    p = PythonSubprocess(script_path, debug_stdout=debug_stdout)
    p.start()
    yield p
    p.kill()
    
def test_PythonSubprocess():
    p = PythonSubprocess('server.py')
    p.start()
    time.sleep(0.5)
    p.kill()
    stdout_str = p.stdout.strip()
    assert stdout_str == "ChatServer starting up on port 3001"

def test_AutoPythonSubprocess():
    with AutoPythonSubprocess('server.py') as p:
        time.sleep(0.5)
    assert p.stdout.strip() == "ChatServer starting up on port 3001"

@contextlib.contextmanager
def simple_client(address, name):
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(address)
    prompt = sock.recv(100).rstrip()
    assert prompt == "Enter your name:"
    sock.sendall(name + "\n")
    yield sock
    sock.close()

def test_one_client():
    with AutoPythonSubprocess('server.py') as server:
        assert server.wait_line() == "ChatServer starting up on port 3001"
        with simple_client(('127.0.0.1', 3001), "Aaron") as client:
            assert server.wait_line() == "Aaron joined chat."
            client.sendall("test\n")
            assert server.wait_line() == "Aaron:test"
        assert server.wait_line() == "Aaron left chat."

def test_two_clients():
    service = ('127.0.0.1', 3001)
    with AutoPythonSubprocess('server.py', debug_stdout=False) as server:
        assert server.wait_line() == "ChatServer starting up on port 3001"
        with simple_client(service, "client1") as client1, simple_client(service, "client2") as client2:
            assert server.wait_line() == "client1 joined chat."
            assert server.wait_line() == "client2 joined chat."
            client1.sendall("test\n")
            assert server.wait_line() == "client1:test"
            client2_message = client2.recv(100).rstrip()
            assert client2_message == "client1: test"
            client2.sendall("test\n")
            assert server.wait_line() == "client2:test"
            client1_message = client1.recv(100).rstrip()
            assert client1_message == "client2: test"
            
        assert server.wait_line() == "client2 left chat."
        assert server.wait_line() == "client1 left chat."

test_AutoPythonSubprocess()
test_two_clients()

