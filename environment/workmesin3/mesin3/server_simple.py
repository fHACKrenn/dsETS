import sys
import zmq
from os import listdir
from os.path import isfile, join

HOSTNAME = "mesin3"
FILEPATH = "/home/jovyan/work/mesin1/files"
NEWLINE = "\n"

ERRN = "ERRN".encode("utf-8")
MESG = "MESG".encode("utf-8")
FILE = "FILE".encode("utf-8")

if len(sys.argv) < 2:
    print("I: Syntax: %s <endpoint>" % sys.argv[0])
    sys.exit(0)

endpoint = sys.argv[1]
context = zmq.Context()
server = context.socket(zmq.REP)
server.bind(endpoint)

print(f"I: Server {HOSTNAME} is ready at {endpoint}")

while True:
    msg = server.recv_multipart()
    if not msg or len(msg) < 1:
        break

    command = msg[0].decode("utf-8")
    filename = msg[1].decode("utf-8") if len(msg) > 1 else None

    if command == "list":
        files = [f for f in listdir(FILEPATH) if isfile(join(FILEPATH, f))]
        res = [HOSTNAME.encode("utf-8"), MESG, f"Files in {HOSTNAME}:\n{NEWLINE.join(files)}".encode("utf-8")]
    elif command == "download" and filename:
        if isfile(join(FILEPATH, filename)):
            with open(join(FILEPATH, filename), "rb") as f:
                content = f.read()
            res = [HOSTNAME.encode("utf-8"), FILE, filename.encode("utf-8"), content]
        else:
            res = [HOSTNAME.encode("utf-8"), ERRN, "ERROR: No such file exists".encode("utf-8")]
    else:
        res = [HOSTNAME.encode("utf-8"), ERRN, "ERROR: Invalid command".encode("utf-8")]

    server.send_multipart(res)

# Clean up context (this line will not be reached in a while True loop)
context.term()
