import socket
import threading
import re


class ClientListener(threading.Thread):
    """Thread chargé de recevoir les messages d'un client."""

    def __init__(self, server, client_socket, address):
        super().__init__()
        self.server = server
        self.socket = client_socket
        self.address = address
        self.username = "Utilisateur"
        self.listening = True
        self.disconnected = False
        self.disconnect_lock = threading.Lock()

    def run(self):
        buffer = b""

        try:
            while self.listening:
                data = self.socket.recv(4096)

                if not data:
                    break

                buffer += data

                # Un message se termine par le caractère retour à la ligne.
                while b"\n" in buffer:
                    raw_message, buffer = buffer.split(b"\n", 1)

                    try:
                        message = raw_message.decode("utf-8").strip()
                    except UnicodeDecodeError:
                        print("Message reçu avec un encodage invalide.")
                        return

                    if message:
                        self.handle_msg(message)

        except OSError as error:
            if self.listening:
                print(f"Erreur de réception avec {self.address} : {error}")
        finally:
            self.quit()

    def handle_msg(self, data):
        print(f"{self.address} : {data}")

        username_result = re.fullmatch(r"USERNAME (.+)", data)
        if username_result:
            self.username = username_result.group(1).strip()
            if self.username:
                self.server.echo(f"ℹ️ {self.username} a rejoint le chat.\n")
            return

        if data == "QUIT":
            self.quit()
            return

        # Le client transmet déjà le nom devant le message.
        self.server.echo(data + "\n")

    def quit(self):
        with self.disconnect_lock:
            if self.disconnected:
                return
            self.disconnected = True
            self.listening = False

        self.server.remove_socket(self.socket)

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.socket.close()
        except OSError:
            pass

        self.server.echo(f"ℹ️ {self.username} a quitté le chat.\n")
        print(f"Déconnexion de {self.address}")
