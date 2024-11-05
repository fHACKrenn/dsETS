import sys
import zmq
import time

GLOBAL_TIMEOUT = 2500  # Timeout for polling in milliseconds

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
        # Prefix request with sequence number and empty envelope
        self.sequence += 1
        msg = [b'', str(self.sequence).encode()] + [r.encode() for r in request]

        # Send the request to all connected servers
        for _ in range(self.servers):
            self.socket.send_multipart(msg)

        # Poll for a reply from any of the endpoints
        poll = zmq.Poller()
        poll.register(self.socket, zmq.POLLIN)

        reply = None
        endtime = time.time() + GLOBAL_TIMEOUT / 1000.0

        while time.time() < endtime:
            socks = dict(poll.poll((endtime - time.time()) * 1000))
            if socks.get(self.socket) == zmq.POLLIN:
                reply = self.socket.recv_multipart()
                if len(reply) >= 3:
                    return reply

        print("Error: No response received within the timeout.")
        return []

    def handle_command(self, command):
        if command == 'list':
            reply = self.request("LIST")
            if reply and len(reply) >= 4 and reply[2] == b"OK":
                file_list = reply[3].decode().split("\n")  # Corrected index to 3

                print("Files available for download:")
                for i, file_name in enumerate(file_list):
                    print(f"{i}. {file_name}")
            else:
                print("Error: Unable to retrieve the file list from the server.")

        elif command == 'download':
            file_name = input("Enter file name to download: ").strip()
            reply = self.request(f"GET {file_name}")
            if reply and len(reply) >= 4 and reply[2] == b"OK":
                file_content = reply[3]  # Corrected index to 3
                local_file_path = f"./{file_name}"
                with open(local_file_path, 'wb') as f:
                    f.write(file_content)
                print(f"File '{file_name}' has been downloaded and saved as '{local_file_path}'")
            else:
                print(f"Error: {reply[3].decode()}")

        elif command == 'exit':
            print("Exiting the client.")
            return False  # Returning False will exit the loop

        else:
            print("Invalid command. Use list, download, or exit.")
        return True


def main():
    # Update the check to allow both single and multiple endpoints
    if len(sys.argv) < 2:
        print("Usage: python client_brutal.py <endpoint1> [<endpoint2> ...]")
        sys.exit(0)

    endpoints = sys.argv[1:]
    client = FLClient()

    # Try to connect to all endpoints
    connected = False
    for endpoint in endpoints:
        try:
            client.connect(endpoint)
        except Exception as e:
            print(f"Error connecting to {endpoint}: {e}")

    if client.servers == 0:
        print("Error: Could not connect to any endpoint.")
        sys.exit(1)

    # Now continuously ask for commands until the user exits
    while True:
        print("\nAvailable commands:")
        print("1. list  -> List available files")
        print("2. download -> Download a file")
        print("3. exit  -> Exit the client")

        command = input("\nEnter command: ").strip().lower()

        if not client.handle_command(command):
            break  # Exit the loop if the user enters 'exit'

    client.destroy()


if __name__ == "__main__":
    main()
