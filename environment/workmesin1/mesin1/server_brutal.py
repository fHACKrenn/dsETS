import os
import zmq
import sys

# Check if port is passed as an argument
if len(sys.argv) < 2:
    print("Usage: python server_brutal.py tcp://*:<port>")
    sys.exit(1)

endpoint = sys.argv[1]
files_directory = "/home/jovyan/work/mesin1/files/"

# Initialize ZMQ server
context = zmq.Context()
server = context.socket(zmq.REP)
server.bind(endpoint)

print(f"I: Service is ready at {endpoint}")

while True:
    request = server.recv_multipart()  # Receive multipart request
    print(f"Received request: {request}")

    if not request:
        break

    command = request[1].decode()

    if command == "LIST":
        files = os.listdir(files_directory)
        files = [f for f in files if os.path.isfile(os.path.join(files_directory, f))]
        file_list = "\n".join(files)
        print(f"Sending file list: {file_list}")
        reply = [b"", b"OK", file_list.encode()]
    
    elif command.startswith("GET "):
        file_name = command[4:].strip()
        file_path = os.path.join(files_directory, file_name)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                file_content = f.read()
            reply = [b"", b"OK", file_content]
            print(f"Sending file '{file_name}' to client.")
        else:
            reply = [b"", b"ERROR", b"File not found"]
            print(f"File '{file_name}' not found.")
    
    else:
        reply = [b"", b"ERROR", b"Invalid command"]

    server.send_multipart(reply)  # Send the response
