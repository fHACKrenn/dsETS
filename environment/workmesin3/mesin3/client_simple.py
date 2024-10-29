import sys
import zmq
import argparse

REQUEST_TIMEOUT = 1000
MAX_RETRIES = 3

ERRN = "ERRN".encode("utf-8")
MESG = "MESG".encode("utf-8")
FILE = "FILE".encode("utf-8")

def send_request(ctx, endpoint, request):
    print(f"I: Sending request to {endpoint}...")
    client = ctx.socket(zmq.REQ)
    client.setsockopt(zmq.LINGER, 0)
    client.connect(endpoint)
    client.send_multipart(request)
    poll = zmq.Poller()
    poll.register(client, zmq.POLLIN)
    socks = dict(poll.poll(REQUEST_TIMEOUT))
    if socks.get(client) == zmq.POLLIN:
        reply = client.recv_multipart()
    else:
        reply = None
    poll.unregister(client)
    client.close()
    return reply

# Setup command-line argument parsing
parser = argparse.ArgumentParser(description="File Client")
parser.add_argument('endpoint', help="ZMQ endpoint to connect to (e.g., tcp://localhost:5555)")
subparsers = parser.add_subparsers(dest="command", help="Sub-command (list or download)")

# Sub-command for --list
parser_list = subparsers.add_parser('list', help="List files on the server")

# Sub-command for --download
parser_download = subparsers.add_parser('download', help="Download a file from the server")
parser_download.add_argument('filename', help="The name of the file to download")

# Parse the command-line arguments
args = parser.parse_args()

# Create ZMQ context
context = zmq.Context()

if args.command == "list":
    request = ["list".encode("utf-8")]
elif args.command == "download":
    request = ["download".encode("utf-8"), args.filename.encode("utf-8")]
else:
    print("Invalid command. Usage : python flclient2.py {endpoint} {list,download}")
    sys.exit(1)

# Send request to the endpoint and receive the reply
reply = send_request(context, args.endpoint, request)

if reply:
    if reply[1] == ERRN:
        print(f"Error from {reply[0].decode('utf-8')}: {reply[2].decode('utf-8')}")
    elif reply[1] == MESG:
        print(f"Message from {reply[0].decode('utf-8')}:\n{reply[2].decode('utf-8')}")
    elif reply[1] == FILE:
        filename = reply[2].decode("utf-8")
        with open(filename, "wb") as f:
            f.write(reply[3])
        print(f"File {filename} downloaded successfully")
else:
    print("No response from server.")
