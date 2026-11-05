
import socket  # AMÉLIORATION : importe le module complet pour accéder aux exceptions socket.error et aux fonctions réseau
import threading  # creer et gérer les threads
import re  # manipuler des expressions
import time  # gerer le temps


class ClientListener(threading.Thread):  # qui hérite de thread
    """Classe ClientListener : gère la communication avec un client.
    Chaque instance fonctionne dans un thread indépendant """

    def __init__(self, server, socket, address):
        """ Initialise le thread associé à un client
        self: lobjet lui meme
        server: référence vers le serveur principal.
        socket: socket de communication avec le client.
        address: adresse IP et port du client """

        super(ClientListener, self).__init__()  # Initialise la classe Thread

        self.server = server  # enregistre une reference vers le server
        self.socket = socket  # enregistre le socket du client
        self.address = address  # enregistre ladresse du client

        self.listening = True  # Indique si le thread doit continuer à écouter

        self.username = "No username"  # Nom par défaut du client

        # AMÉLIORATION : permet de savoir si la déconnexion a déjà été effectuée
        self.disconnected = False

    def run(self):
        """Fonction exécutée automatiquement au démarrage du thread.
        Elle reçoit les messages envoyés par le client."""

        # AMÉLIORATION 2 : crée un tampon pour stocker temporairement les données reçues
        buffer = b""

        while self.listening:
            try:
                # Reçoit les données envoyées par le client
                data = self.socket.recv(1024)

                # AMÉLIORATION : détecte la fermeture de la connexion par le client
                if not data:
                    print("Le client s'est déconnecté :", self.address)
                    self.quit()
                    break

                # AMÉLIORATION 2 : ajoute les nouvelles données au tampon
                buffer += data

                # AMÉLIORATION 2 : recherche les messages complets grâce au séparateur \n
                while b"\n" in buffer:

                    # AMÉLIORATION 2 : sépare le premier message du reste des données
                    message, buffer = buffer.split(b"\n", 1)

                    try:
                        # AMÉLIORATION 2 : décode le message complet en texte UTF-8
                        message = message.decode("UTF-8")

                    except UnicodeDecodeError:
                        print("Message reçu avec un encodage invalide.")
                        self.quit()
                        break

                    # AMÉLIORATION 2 : traite uniquement les messages complets
                    if self.listening:
                        self.handle_msg(message)

            # AMÉLIORATION : capture les erreurs liées à la réception réseau
            except socket.error as erreur:
                print("Erreur lors de la réception :", erreur)
                self.quit()
                break

        print("Ending client thread for", self.address)

    def quit(self):
        """Déconnecte le client et informe les autres clients de son départ"""

        # AMÉLIORATION : évite de traiter plusieurs fois la même déconnexion
        if self.disconnected:
            return

        self.disconnected = True
        self.listening = False  # Arrête la boucle d'écoute

        try:
            self.socket.close()  # Ferme la socket du client

        # AMÉLIORATION : gère une éventuelle erreur pendant la fermeture
        except socket.error as erreur:
            print("Erreur lors de la fermeture de la connexion :", erreur)

        self.server.remove_socket(self.socket)  # Retire le client de la liste du serveur

        # AMÉLIORATION 2 : informe les autres clients du départ avec un message terminé par \n
        self.server.echo("{0} has quit.\n".format(self.username))

    def handle_msg(self, data):
        """ Analyse le message reçu et détermine l'action à effectuer
             data : message reçu du client."""

        print(self.address, "sent :", data)

        # Recherche une commande permettant de définir le nom du client
        username_result = re.search('^USERNAME (.*)$', data)

        """ ^: debut du text
             .* : capture tout ce qui suit
                $: fin de text"""

        if username_result:

            self.username = username_result.group(1)  # Récupère et enregistre le nom du client

            # AMÉLIORATION 2 : informe les autres clients avec un message terminé par \n
            self.server.echo("{0} has joined.\n".format(self.username))

        elif data == "QUIT":

            self.quit()  # Déconnecte le client s'il demande à quitter le chat

        elif data == "":

            self.quit()  # Déconnecte le client si la connexion est fermée

        else:

            # AMÉLIORATION 2 : ajoute \n pour délimiter le message envoyé aux autres clients
            self.server.echo(data + "\n")
