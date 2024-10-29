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
parser.add_argument('endpoints', nargs='+', help="ZMQ endpoints to connect to (e.g., tcp://localhost:5555)")

# Sub-command for --list
parser.add_argument('--list', action='store_true', help="List files on the server")

# Sub-command for --download
parser.add_argument('--download', type=str, help="Download a file from the server. Specify the filename.")

# Parse the command-line arguments
args = parser.parse_args()

# Create ZMQ context
context = zmq.Context()

# Prepare the request based on the command
if args.list:
    request = ["list".encode("utf-8")]
elif args.download:
    request = ["download".encode("utf-8"), args.download.encode("utf-8")]
else:
    print("Invalid command. Usage: python client_simple.py {endpoints} [--list | --download filename]")
    sys.exit(1)

# Iterate through the endpoints
for endpoint in args.endpoints:
    reply = send_request(context, endpoint, request)
    
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
        break  # Stop after a successful request
    else:
        print(f"No response from {endpoint}.")

# Clean up context
context.term()
