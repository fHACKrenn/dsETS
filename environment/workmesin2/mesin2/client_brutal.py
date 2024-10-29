import sys
import zmq

# Client class for interacting with the server
class FLClient:
    def __init__(self):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)  # REQ socket for request-response
        self.socket.setsockopt(zmq.LINGER, 0)

    def connect(self, endpoint):
        self.socket.connect(endpoint)
        print(f"Connected to {endpoint}")

    def send_request(self, request):
        self.socket.send_multipart([b"", request.encode()])
        reply = self.socket.recv_multipart()  # Receive the server's reply
        return reply

    def close(self):
        self.socket.close()
        self.context.term()

# Main logic for the client
def main():
    if len(sys.argv) < 3:
        print("Usage: client.py <endpoint> <command> [<file_name>]")
        sys.exit(0)

    endpoint = sys.argv[1]
    command = sys.argv[2].lower()  # Handle case sensitivity
    client = FLClient()
    client.connect(endpoint)

    if command == "list":
        reply = client.send_request("LIST")
        if reply[1] == b"OK":
            file_list = reply[2].decode()
            print("Files available for download:")
            print(file_list)
        else:
            print("Error: Unable to retrieve file list.")

    elif command == "download":
        if len(sys.argv) < 4:
            print("Error: File name required for download.")
            sys.exit(1)

        file_name = sys.argv[3]
        reply = client.send_request(f"GET {file_name}")
        if reply[1] == b"OK":
            with open(file_name, 'wb') as f:
                f.write(reply[2])
            print(f"File '{file_name}' has been downloaded.")
        else:
            print(f"Error: {reply[2].decode()}")

    else:
        print("Invalid command. Use 'list' or 'download <filename>'.")

    client.close()

if __name__ == "__main__":
    main()
