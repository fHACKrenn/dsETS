import sys
import zmq

GLOBAL_TIMEOUT = 2500  # ms

class FLClient(object):
    def __init__(self):
        self.servers = 0
        self.sequence = 0
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.DEALER)

    def destroy(self):
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.close()
        self.context.term()

    def connect(self, endpoint):
        self.socket.connect(endpoint)
        self.servers += 1
        print(f"I: Connected to {endpoint}")

    def request(self, *request):
        self.sequence += 1
        msg = [b'', str(self.sequence).encode()] + [r.encode() for r in request]
        replies = []

        for server in range(self.servers):
            self.socket.send_multipart(msg)

        poll = zmq.Poller()
        poll.register(self.socket, zmq.POLLIN)

        while True:
            socks = dict(poll.poll(GLOBAL_TIMEOUT))
            if socks.get(self.socket) == zmq.POLLIN:
                reply = self.socket.recv_multipart()
                assert len(reply) >= 3
                replies.append(reply)

        return replies


def main():
    if len(sys.argv) < 3:
        print("Usage: python client_brutal.py <endpoint1> <endpoint2> ...")
        sys.exit(0)

    endpoints = sys.argv[1:]
    client = FLClient()

    # Try to connect to each endpoint, and once connected to one, stop trying the others
    connected = False
    for endpoint in endpoints:
        try:
            client.connect(endpoint)
            print(f"Connected to {endpoint}")
            connected = True
            break  # Stop after the first successful connection
        except Exception as e:
            print(f"Error connecting to {endpoint}: {e}")
            continue

    if not connected:
        print("Error: Could not connect to any endpoint.")
        sys.exit(1)

    # Now list available commands
    print("\nAvailable commands:")
    print("1. --list  -> List available files")
    print("2. --download <file_name> -> Download a file")

    command = input("\nEnter command: ").strip().lower()

    if command == 'list' or command == '--list':
        reply = client.request("LIST")
        if reply and reply[0][2] == b"OK":
            file_list = reply[0][3].decode().split("\n")
            print("Files available for download:")
            for i, file_name in enumerate(file_list):
                print(f"{i}. {file_name}")
        else:
            print("Error: Unable to retrieve the file list from the server.")
    
    elif command.startswith('download') or command == '--download':
        file_name = input("Enter file name to download: ").strip()
        reply = client.request(f"GET {file_name}")
        if reply and reply[0][2] == b"OK":
            file_content = reply[0][3]
            local_file_path = f"./{file_name}"
            with open(local_file_path, 'wb') as f:
                f.write(file_content)
            print(f"File '{file_name}' has been downloaded and saved as '{local_file_path}'")
        else:
            print(f"Error: {reply[0][3].decode()}")
    
    else:
        print("Invalid command. Use --list or --download.")

    client.destroy()


if __name__ == "__main__":
    main()
