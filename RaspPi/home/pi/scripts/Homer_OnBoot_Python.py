import json
import MySQLdb
import socket
import time

#DataBase Connection
dataBase = MySQLdb.connect(host = 'localhost',
                           user = 'root',
                           passwd = 'H0m3r',
                           db = 'homer')

# Functions
#Convert String to JSON
def convert_String_ToJSON( arduinoData ):
    stringArray = arduinoData.split(',')

    json_file = dict([(k, v) for k,v in zip (stringArray[::2], stringArray[1::2])])
    
    try:
        return json.dumps(json_file, sort_keys=True)
   
    except (ValueError, KeyError, TypeError):
        print ("JSON ERROR")


#Store JSON into Database
def dBJSON_Store(json_file,NodeID):
    cursor = dataBase.cursor()
    cursor.execute("Insert into Sensor_Log(Date,NodeID,Data) values(NOW(),%s,%s)",(NodeID,json_file))

    dataBase.commit()

#Send Request to Arduino for Sensor information
def arduino_Data_Request(NodeIP):
    HOST, PORT = NodeIP, 8888

    # SOCK_DGRAM is the socket type to use for UDP sockets
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # As you can see, there is no connect() call; UDP has no connections.
    # Instead, data is directly sent to the recipient via sendto().
    sock.sendto("pull" + "\n", (HOST, PORT))
    received = sock.recv(1024)
    return received;

#Fetch an Associative Array from MySQL database
def mysql_fetch_assoc():
	out = []  
	try:
		cursor = dataBase.cursor()
		cursor.execute("Select NodeID,IP from Nodes")
		rows = cursor.fetchall()    
		for row in rows:        
			data ={}
			for i in range(len(row)):          
			    if row[i] != None:                        
				    tmp = cursor.description            
				    data[tmp[i][0]] = row[i]
                out.append(data)     
	except Exception as err:
		print("Error in fetchassoc:")
		print(err)
	finally:
	    return out	

#Checks to see if the last data entry matches if so, do not store in Database
def check_duplicate_data(NodeID,json_file):
    try:
        cursor = dataBase.cursor()
        cursor.execute("Select Data from Sensor_Log where NodeID = %s ORDER BY Date DESC LIMIT 1",(NodeID))
        previous_data = ''.join(cursor.fetchone())
        if previous_data == json_file:
            return True
        else:
            return False
    except Exception as err:
        print("Error checking duplicate data")
        print(err)

#Runs Forever
while True:
    for node in mysql_fetch_assoc():
        arduinoData = arduino_Data_Request(node['IP'])
        print(arduinoData)
        json_file = convert_String_ToJSON(arduinoData)
        if check_duplicate_data(node['NodeID'],json_file) == False:
            dBJSON_Store(json_file,node['NodeID']);
        time.sleep(5)
  
