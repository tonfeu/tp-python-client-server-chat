import socket
import threading
import queue


class Client:
    """Client TCP : connexion, envoi et réception des messages."""

    def __init__(self, username, server, port):
        self.username = username.strip()
        self.server = server
        self.port = port
        self.listening = False

        # File d'attente partagée entre le thread réseau et Tkinter.
        self.message_queue = queue.Queue()
        self.send_lock = threading.Lock()
        self.listen_thread = None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.socket.connect((server, port))
            self.listening = True
            self.send(f"USERNAME {self.username}")
        except OSError:
            self.socket.close()
            raise

    def listen(self):
        """Démarre le thread qui reçoit les messages sans bloquer Tkinter."""
        if self.listen_thread is None or not self.listen_thread.is_alive():
            self.listen_thread = threading.Thread(target=self.listener, daemon=True)
            self.listen_thread.start()

    def listener(self):
        buffer = b""

        try:
            while self.listening:
                data = self.socket.recv(4096)
                if not data:
                    self.message_queue.put("La connexion avec le serveur a été fermée.")
                    break

                buffer += data
                while b"\n" in buffer:
                    raw_message, buffer = buffer.split(b"\n", 1)
                    try:
                        message = raw_message.decode("utf-8")
                    except UnicodeDecodeError:
                        self.message_queue.put("Erreur : message reçu avec un encodage invalide.")
                        continue

                    if message:
                        self.handle_msg(message)

        except OSError as error:
            if self.listening:
                self.message_queue.put(f"Erreur réseau : {error}")
        finally:
            self.tidy_up()

    def send(self, message):
        """Envoie une ligne au serveur."""
        if not self.listening:
            return False

        message = message.strip()
        if not message:
            return False

        # Les commandes USERNAME et QUIT ne reçoivent pas de préfixe.
        if message != "QUIT" and not message.startswith("USERNAME "):
            message = f"{self.username}: {message}"

        try:
            with self.send_lock:
                self.socket.sendall((message + "\n").encode("utf-8"))
            return True
        except OSError as error:
            self.message_queue.put(f"Erreur pendant l'envoi : {error}")
            self.tidy_up()
            return False

    def handle_msg(self, data):
        """Place le message reçu dans la file que l'interface consulte."""
        if data == "QUIT":
            self.tidy_up()
        elif data:
            self.message_queue.put(data)

    def tidy_up(self):
        """Ferme la connexion une seule fois."""
        if not self.listening:
            return

        self.listening = False
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass

        try:
            self.socket.close()
        except OSError:
            pass


if __name__ == "__main__":
    try:
        username = input("Nom d'utilisateur : ").strip()
        server = input("Adresse IP du serveur : ").strip()
        port = int(input("Port : "))

        client = Client(username, server, port)
        client.listen()

        print("Connecté. Écris un message (QUIT pour quitter).")
        while client.listening:
            try:
                message = input()
            except EOFError:
                break

            if message.upper() == "QUIT":
                client.send("QUIT")
                break

            client.send(message)

        client.tidy_up()

    except ValueError:
        print("Le port doit être un nombre entier.")
    except OSError as error:
        print("Connexion impossible :", error)
    except KeyboardInterrupt:
        print("\nDéconnexion demandée.")
