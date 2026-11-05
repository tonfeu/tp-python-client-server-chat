
import threading
import socket
import re
import queue


class Client:
    """
    Classe Client : représente un utilisateur du chat.
    Elle permet de se connecter au serveur, d'envoyer
    et de recevoir des messages.
    """

    def __init__(self, username, server, port):

        self.username = username
        self.listening = False

        # File d'attente pour transmettre les messages à Tkinter
        self.messages = queue.Queue()

        try:
            self.socket = socket.socket(
                socket.AF_INET,
                socket.SOCK_STREAM
            )

            self.socket.connect((server, port))

            self.listening = True

            # Envoi du nom d'utilisateur au serveur
            self.send("USERNAME {0}".format(username))

        except OSError:
            print("Impossible de joindre le serveur.")
            raise

    def listener(self):
        """
        Reçoit les messages du serveur.
        """

        buffer = b""

        while self.listening:

            try:
                data = self.socket.recv(1024)

                if not data:
                    self.messages.put("Vous avez été déconnecté du serveur.")
                    break

                buffer += data

                while b"\n" in buffer:

                    message, buffer = buffer.split(b"\n", 1)

                    try:
                        message = message.decode("UTF-8")

                    except UnicodeDecodeError:
                        self.messages.put("Erreur d'encodage.")
                        break

                    self.handle_msg(message)

            except OSError as erreur:

                if self.listening:
                    self.messages.put(
                        "Erreur de réception : {0}".format(erreur)
                    )

                break

        self.tidy_up()

    def listen(self):
        """
        Démarre un thread indépendant pour recevoir les messages.
        """

        self.listen_thread = threading.Thread(
            target=self.listener,
            daemon=True
        )

        self.listen_thread.start()

    def send(self, message):
        """
        Envoie un message au serveur.
        """

        if not self.listening:
            return

        if message.strip() == "" and message != "QUIT":
            return

        try:

            username_result = re.search(
                '^USERNAME (.*)$',
                message
            )

            if not username_result and message != "QUIT":

                message = "{0}: {1}".format(
                    self.username,
                    message
                )

            message += "\n"

            self.socket.sendall(message.encode("UTF-8"))

        except OSError as erreur:

            self.messages.put(
                "Erreur lors de l'envoi : {0}".format(erreur)
            )

            self.tidy_up()

    def tidy_up(self):
        """
        Ferme la connexion.
        """

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

    def handle_msg(self, data):
        """
        Place les messages reçus dans la file d'attente.
        Tkinter les récupérera ensuite.
        """

        if data == "QUIT":
            self.tidy_up()

        elif data == "":
            self.tidy_up()

        else:
            self.messages.put(data)
