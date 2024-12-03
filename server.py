
import socket
import threading
import sqlite3
import ast
def create_game(val):
    val = ast.literal_eval(val)
    sqliteConnection = sqlite3.connect("rooms.db")
    cursor = sqliteConnection.cursor()
    values = [x for x in val]
    print(values)
    try:
        cursor.execute("INSERT INTO rooms ('room_name','room_password','creator_name','game_size','game_link') VALUES (?,?,?,?,?)",(values[0],values[1],values[2],values[3],values[4]))
        sqliteConnection.commit()
        return "Success"
    except:
        return "Failed"
def get_game(room_link,addr):
    sqliteConnection = sqlite3.connect("rooms.db")
    cursor = sqliteConnection.cursor()
    cursor.execute("SELECT * from rooms WHERE game_link=?",(room_link,))
    result = cursor.fetchall()
    result = [x for x in result[0]]
    result.append(addr)
    print(result)
    print(type(result))
    return result
def on_new_client(clientsocket,addr):
    while True:
        msg = clientsocket.recv(1024)
        msg = msg.decode("utf-8")

        if len(msg) != 0 :
            if msg == "quitserver":
                clientsocket.close()
                
            if msg.startswith("GETGAME"): 
                game = get_game(msg.split("|")[1],addr)
                return_message = str(game)
            elif msg.startswith("CREATEGAME"): 
                val = msg.split("|")[1]
                try:
                    c_g = create_game(val)
                    return_message = f"Success|{addr}" if c_g else "Failed"

                except:
                    return_message = "FAILED EXCEPTION ERROR"
            elif msg.startswith("MOVE"):
                move = msg.split("|")[1]
                try:
                    move = ast.literal_eval(move)
                    print("move had no issue move: ",move)
                except ValueError:
                    print("move had value error move: ", move)
                #burdaki problem move bilgileri alınıp karşı tarafa gönderildiğinde karşı tarafta bunu dinleyen bi
                #fonksiyon yok 
                #bu fonksiyon thread ile dinleyecek şekilde ayarlanabilir ama asıl bağlantının bozulmasına sebep olabilr 
                # just save moves in db 
                return_message = str(move)
            
            else:
                return_message = f"Message not correct format GETGAME: {msg.startswith('GETGAME')} CREATEGAME: {msg.startswith('CREATEGAME')} MESSAGE: {msg}"
        else:
            return_message = "Message was empty"

        clientsocket.send(bytes(return_message,"utf-8"))

s = socket.socket()
host = "127.0.0.1"
port = 65434

s.bind((host, port))
s.listen(5)
stop_event = threading.Event()
threads = []
try:
        
    while True:
        c, addr = s.accept()
        print(addr)
        x = threading.Thread(target = on_new_client, args = [c,addr]).start()
        threads.append(x)
except KeyboardInterrupt:
    print("Closing..")
    stop_event.set()
    s.close()
    for thread in threads:
        thread.join()
finally:
    for thread in threads:
        thread.join()
    s.close()

    print("All threads stopped. Exiting program.")