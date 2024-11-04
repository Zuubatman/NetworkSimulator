from socket import *
import threading
serverName = 'localhost'

serverPort = 40000

clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(2)

#Thread para ouvir as respostas do servidor       
def listen():
    while(True):
        try:
            response, _  = clientSocket.recvfrom(2048)
            print (response.decode())
            
        except timeout:  
            continue  

        except  ():
            if not threading.main_thread().is_alive(): break

#Thread para enviar respostas ao servidor        
def sendToServer():    
    print("Insert a Command:")
    while(True):
        command = input("")
        
        if('pmf' in command):
            dataArr = command.split(' ')
            userDestination = dataArr[1]
            
            filePath = input("Insert file path:")
            with open(filePath, 'rb') as file:
                content = file.read()
               
            message = 'file '+ userDestination+ ' <file> \n'+ content.decode() 
            clientSocket.sendto(message.encode(),(serverName, serverPort))
            
        elif(command == "end"):
            clientSocket.close()
    
        else:
            clientSocket.sendto(command.encode(),(serverName, serverPort))


#Icialização das Threads, uma para ouvir o servidor e outra pra enviar respostas
def run():
    threading.Thread(target=listen).start()
    threading.Thread(target=sendToServer).start()

run()    
    