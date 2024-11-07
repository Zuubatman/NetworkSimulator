from socket import *
import threading

serverPort = 40000

customIP = '10.17.141.103'

serverSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.bind((customIP, serverPort))

serverSocket.settimeout(2)

table = []      

def listen():
    print("Router is Listening...")
    while (True):

        try:
            command, clientAddress = serverSocket.recvfrom(2048)
            print(F"Listening Address: {clientAddress}")
            print(command)

        except timeout:      
            continue
        
        except  (e):
            print(e)

def addInTable(neighborIp, dist, exitIp):
    table.append({'neighborIp': neighborIp, 'dist': dist, 'exitIp': exitIp})


def readNeighbors():
    neighborsFile = input("Insira o caminho para o arquivo: ")

    with open(neighborsFile, 'rb') as file:
            neighborsRaw = file.read()
               
    neighborsStr = neighborsRaw.decode('utf-8')

    neighbors = neighborsStr.split(',')
        
    for i in neighbors:
        routerAddress = (i, 40000)
        addInTable(i, 1, routerAddress)
        serverSocket.sendto('Joia'.encode(), routerAddress)


def run () :
    print(f"Starting Router {serverSocket}")
    threading.Thread(target=listen).start()
    readNeighbors()


run()
