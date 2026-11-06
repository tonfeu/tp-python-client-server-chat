import socket  # AMÉLIORATION : importe le module complet pour accéder aux exceptions socket.error et aux fonctions réseau
import threading # creer et gérer les threads
import re # manipuler des expressions
import time # gerer le temps


class ClientListener(threading.Thread): # qui hérite de thread
    """Classe ClientListener : gère la communication avec un client.
    Chaque instance fonctionne dans un thread indépendant """

    def __init__(self, server, socket, address):
        """ Initialise le thread associé à un client
        self: lobjet lui meme
        server: référence vers le serveur principal.
        socket: socket de communication avec le client.
        address: adresse IP et port du client """

        super(ClientListener, self).__init__()  # Initialise la classe Thread

        self.server = server # enregistre une reference vers le server
        self.socket = socket #enregistre le socket du client
        self.address = address# enregistre ladresse du client

        self.listening = True# Indique si le thread doit continuer à écouter

        self.username = "No username"  # Nom par défaut du client

        # AMÉLIORATION : permet de savoir si la déconnexion a déjà été effectuée
        self.disconnected = False

    def run(self):
        """Fonction exécutée automatiquement au démarrage du thread.
        Elle reçoit les messages envoyés par le client. """

        while self.listening:
            try:
                # Reçoit les données envoyées par le client
                data = self.socket.recv(1024)

                """La méthode recv() permet de recevoir les données envoyées par le client.
               Le nombre 1024 représente la quantité maximale d'octets que Python essaie de lire lors de cet appel.
               Cela ne signifie pas que le message doit obligatoirement faire 1024 octets"""

                # AMÉLIORATION : recv() retourne des données vides lorsque le client ferme sa connexion
                if not data:
                    print("Le client s'est déconnecté :", self.address)
                    self.quit()
                    break

                # AMÉLIORATION : transforme les octets reçus en texte UTF-8
                data = data.decode('UTF-8')

            # AMÉLIORATION : capture les erreurs liées à la réception réseau
            except socket.error as erreur:
                print("Erreur lors de la réception des données :", erreur)
                self.quit()
                break

            # AMÉLIORATION : détecte les données qui ne peuvent pas être décodées en UTF-8
            except UnicodeDecodeError:
                print("Erreur : le message reçu possède un encodage invalide.")
                self.quit()
                break

            self.handle_msg(data) # traite le message reçu

            time.sleep(0.1)

        print("Ending client thread for", self.address)

    def quit(self):
        """Déconnecte le client et informe les autres clients de son départ"""

        # AMÉLIORATION : évite de traiter plusieurs fois la même déconnexion
        if self.disconnected:
            return

        self.disconnected = True
        self.listening = False  # Arrête la boucle d'écoute

        try:
            self.socket.close() # Ferme la socket du client

        # AMÉLIORATION : gère une éventuelle erreur pendant la fermeture
        except socket.error as erreur:
            print("Erreur lors de la fermeture de la connexion :", erreur)

        self.server.remove_socket(self.socket) # Retire le client de la liste du serveur
        self.server.echo("{0} has quit\n".format(self.username))# Informe les autres clients de son départ

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

            self.username = username_result.group(1) # Récupère et enregistre le nom du client

            self.server.echo("{0} has joined.\n".format(self.username)) # Informe les autres clients de son arrivée

        elif data == "QUIT":

            self.quit() # Déconnecte le client s'il demande à quitter le chat

        elif data == "":

            self.quit()# Déconnecte le client si la connexion est fermée

        else:

            # AJOUT TKINTER : on termine chaque message par un retour à la ligne ("\n"),
            # comme pour "has joined" et "has quit". Ainsi, quand plusieurs messages arrivent
            # dans le même paquet TCP, le client peut les séparer ligne par ligne
            # (nécessaire pour un affichage propre dans la fenêtre Tkinter).
            self.server.echo(data + "\n") # Transmet le message aux clients connectés
              