from socket import *
serverPort = 40000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))

print ("The server is ready to receive")
       
while True:
    message, clientAddress = serverSocket.recvfrom(2048)

    decodedMEssage = message.decode()

    if(decodedMEssage == "fim"):
            serverSocket.sendto('Encerrando conexão...'.encode(), clientAddress)
            break
    else:
        serverSocket.sendto(decodedMEssage.upper().encode(), clientAddress)