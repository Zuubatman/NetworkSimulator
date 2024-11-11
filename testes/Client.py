from socket import *
import threading
import time

serverIP = '192.168.15.130'  # IP do roteador principal (para testes locais, pode ser o mesmo do servidor)
serverPort = 9000
clientSocket = socket(AF_INET, SOCK_DGRAM)
clientSocket.settimeout(2)

# Função para ouvir as respostas do servidor e outras mensagens
def listen():
    while True:
        try:
            response, _ = clientSocket.recvfrom(2048)
            print("Recebido:", response.decode())
        except timeout:
            continue

# Função para enviar comandos ao servidor, incluindo mensagens de texto para roteadores
def sendToServer():
    while True:
        print("\nComandos disponíveis:")
        print("1. REG [username] - Registrar usuário")
        print("2. ALL [message] - Enviar broadcast")
        print("3. PM [destination] [message] - Enviar mensagem privada")
        print("4. SEND [source IP] [destination IP] [message] - Enviar mensagem entre roteadores")
        print("5. END - Encerrar conexão\n")
        
        command = input("Digite um comando: ").strip()
        
        # Registro de usuário
        if command.lower().startswith("reg"):
            clientSocket.sendto(command.encode(), (serverIP, serverPort))
        
        # Envio de broadcast
        elif command.lower().startswith("all"):
            clientSocket.sendto(command.encode(), (serverIP, serverPort))
        
        # Envio de mensagem privada para usuário
        elif command.lower().startswith("pm"):
            clientSocket.sendto(command.encode(), (serverIP, serverPort))
        
        # Envio de mensagem entre roteadores (com roteamento)
        elif command.lower().startswith("send"):
            _, source_ip, dest_ip, *message_parts = command.split()
            message_text = " ".join(message_parts)
            routing_message = f"!{source_ip};{dest_ip};{message_text}"
            clientSocket.sendto(routing_message.encode(), (serverIP, serverPort))
        
        # Encerrar a conexão
        elif command.lower() == "end":
            clientSocket.close()
            break
        
        else:
            print("Comando não reconhecido. Tente novamente.")

# Inicialização das threads para ouvir mensagens e enviar comandos
def run():
    threading.Thread(target=listen, daemon=True).start()
    threading.Thread(target=sendToServer).start()

run()
