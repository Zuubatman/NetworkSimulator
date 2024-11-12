from socket import *
import threading
import time

serverPort = 9000

customIP = '172.20.10.3'

serverSocket = socket(AF_INET, SOCK_DGRAM)

serverSocket.bind((customIP, serverPort))

serverSocket.settimeout(2)

table = []      
lastMSG = {}

def listen():
    print("Router is Listening...")
    while True:
        try:
            message, clientAddress = serverSocket.recvfrom(2048)
            print(f"Listening Address: {clientAddress}")
            msg = message.decode('utf-8')  
            print(msg)

            ipAddress = clientAddress[0]
            lastMSG[ipAddress] = time.time()
            
            if msg.startswith('*'):
                ip = msg[1:]
                addInTable(ip, 1, clientAddress)
                
            elif msg.startswith('@'):
                routes = msg.split('@')[1:]
                compareTable(clientAddress, routes)
                for route in routes:
                    parts = route.split('-')
                    ip = parts[0]  
                    dist = int(parts[1])  
                    v = addInTable(ip, dist+1, clientAddress)
                    if(v==True):
                        routeAnnouncement()
            elif msg.startswith('!'):
                message = msg.split('!')[1:]
                for mess in message:
                    parts = mess.split(';')
                    orig = parts[0]
                    dest = parts[1]
                    mes =  parts[2]
                    if(dest==customIP):
                        print(f'Mensagem recebida.')
                        print(f"{orig}: {mes}")
                    else:
                        for i in table:
                           if i['neighborIp'] == dest:
                            serverSocket.sendto(msg.encode(), i['exitIp'])

        except timeout:      
            continue
        
        except Exception as e:
            print(e)
def sendMSG():
    while True:
        try:
            routerIp = input("Informe o endereço IP do roteador destino: \n")
            message = input("Digite a mensagem que deseja enviar: \n")
            message = '!'+ customIP +';' + routerIp + ';' +message
            for i in table:
                if i['neighborIp'] == routerIp:
                    serverSocket.sendto(message.encode(), i['exitIp'])
                    print(f"Mensagem enviada para {routerIp}: {message}")
                    break
            else: print("Roteador não encontrado na tabela.")
        except timeout:      
            continue
        
        except Exception as e:
            print(e)

def forgotNeighbor():
    while True:
        try:
            currentTime = time.time()
            for neighborIp, lastTime in list(lastMSG.items()):
                if currentTime - lastTime > 35:
                    for i in table:
                        if i['neighborIp'] == neighborIp and i['exitIp'][0]==neighborIp:
                            table.remove(i)
                    print(f"Vizinho {neighborIp} está inativo a mais de 35 segundos e foi removido.")
                    del lastMSG[neighborIp]  
            time.sleep(5)
        except timeout:      
            continue
        
        except Exception as e:
            print(e)

def addInTable(neighborIp, dist, exitIp):
    if neighborIp == customIP or exitIp == serverSocket or neighborIp==exitIp[0]: return False
    for i in table:
        if i['neighborIp'] == neighborIp:
            if dist < i['dist']:
                table.remove(i)
            else:
                return
            break    
    table.append({'neighborIp': neighborIp, 'dist': dist, 'exitIp': exitIp})
    print(f"Tabela adicionada com o ip: {neighborIp} e métrica: {dist}.")
    return True

def compareTable(clientAdress, routes):
    for i in table:
        if i['exitIp'] == clientAdress:
            isOnTable = False
            for route in routes:
                    parts = route.split('-')
                    ip = parts[0]  
                    dist = int(parts[1])  
                    if i['neighborIp'] == ip:
                        isOnTable = True
                        if i['dist'] < dist+1:
                            i['dist'] = i['dist'] +1
            if isOnTable == False:
                table.remove(i)
            isOnTable = False


def sendMSGNeighbor(msg):
    for i in table:
        if(i['dist']==1):
            serverSocket.sendto(msg.encode(), i['exitIp'])

def routeAnnouncement():
    msg =''
    for i in table:
        ip = i['neighborIp']
        dist = i['dist']
        msg += '@' + ip + '-' + str(dist)
    sendMSGNeighbor(msg)

def showRoutesTable():
    msg ='|       IP       |  | Métrica |  |    Origem     |\n'         
    for i in table:
        ip = i['neighborIp']
        dist = i['dist']
        exitIp = i['exitIp'][0]
        msg += f'  ' + ip + '          ' + str(dist) + '         ' + exitIp +  ' \n'
    print(msg)


def scheduleRouteAnnouncement():
    while True:
        routeAnnouncement()
        time.sleep(15)
        routeAnnouncement()
        time.sleep(15)
        showRoutesTable()


def readNeighbors():
    neighborsFile = 'Roteadores.txt'

    with open(neighborsFile, 'rb') as file:
            neighborsRaw = file.read()
               
    neighborsStr = neighborsRaw.decode('utf-8')

    neighbors = neighborsStr.splitlines() 
        
    for i in neighbors:
        routerAddress = (i, 9000)
        serverSocket.sendto(('*'+customIP).encode(), routerAddress)
        addInTable(i, 1, routerAddress)


def run () :
    print(f"Starting Router {serverSocket}")
    threading.Thread(target=listen).start()
    readNeighbors()
    threading.Thread(target=scheduleRouteAnnouncement).start()
    threading.Thread(target=forgotNeighbor).start()
    threading.Thread(target=sendMSG).start()

run()
