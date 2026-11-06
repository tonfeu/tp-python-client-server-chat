# tp-python-client-server-chat
réalisé par 
* cerena mouhleb
* junior tresor


# Application de chat Client-Serveur en Python

## 1. Présentation du projet

Ce projet consiste à développer une application de messagerie instantanée en Python, basée sur une architecture **client-serveur**.

L'application permet à plusieurs utilisateurs de se connecter à un serveur, de choisir un pseudonyme et d'échanger des messages en temps réel.

Le projet utilise :
- **TCP** pour assurer la communication entre le serveur et les clients.
- **UDP** pour rechercher automatiquement les serveurs disponibles sur le réseau local.
- **Le multithreading** pour gérer plusieurs connexions simultanément.
- **Tkinter** pour proposer une interface graphique à l'utilisateur.

L'objectif des améliorations apportées est de rendre l'application plus simple à utiliser, notamment grâce à la découverte automatique des serveurs et à une interface graphique.

## 2. Structure du projet

Le projet est organisé autour de quatre fichiers Python principaux :

| Fichier | Rôle |
|---|---|
| `server.py` | Lance le serveur, accepte les connexions TCP et répond aux demandes de découverte UDP. |
| `client.py` | Gère la connexion au serveur, l'envoi et la réception des messages, ainsi que la découverte des serveurs. |
| `clientthread.py` | Gère individuellement chaque client connecté au serveur et diffuse les messages aux autres utilisateurs. |
| `clientgui.py` | Contient l'interface graphique permettant de se connecter et d'utiliser la messagerie. |

## 3. Prérequis

Pour exécuter le projet, il faut disposer de :

- Python 3 installé sur l'ordinateur.
- Les fichiers du projet.
- Un terminal ou un environnement de développement Python.

Les bibliothèques utilisées sont principalement des bibliothèques standard de Python :

- `socket` : communication réseau TCP et UDP.
- `threading` : gestion des threads.
- `queue` : transmission des événements entre les threads réseau et l'interface graphique.
- `tkinter` : création de l'interface graphique.
- `time`, `sys` et `re` : gestion de différentes opérations du programme.

Aucune installation de bibliothèque externe supplémentaire n'est normalement nécessaire.

## 4. Installation et lancement

### Étape 1 : Récupérer le projet

Télécharger ou cloner le dépôt GitHub sur l'ordinateur.

### Étape 2 : Démarrer le serveur

Ouvrir un terminal dans le dossier du projet et exécuter :

```bash
python server.py
```

Le serveur démarre et attend les connexions des clients. Il peut également demander un nom de serveur, utilisé lors de la découverte automatique.

### Étape 3 : Démarrer un client

Ouvrir un deuxième terminal dans le même dossier et exécuter :

```bash
python clientgui.py
```

L'interface graphique de l'application s'ouvre.

### Étape 4 : Connecter les utilisateurs

Depuis l'interface graphique :

1. Saisir un pseudonyme.
2. Cliquer sur **Rechercher les serveurs**.
3. Sélectionner un serveur dans la liste des serveurs détectés.
4. Cliquer sur **Se connecter**.
5. Une fois connecté, saisir un message dans la zone de saisie.
6. Appuyer sur Entrée ou cliquer sur **Envoyer**.

Pour tester la communication, il est possible de lancer plusieurs clients sur différents terminaux ou ordinateurs.

## 5. Fonctionnement technique

### 5.1. Communication TCP

Le protocole TCP est utilisé pour les échanges de messages entre le serveur et les clients.

Il permet d'établir une connexion entre les deux parties et assure une transmission fiable et ordonnée des données.

Le port TCP utilisé par défaut est :

```text
59001
```

Le serveur centralise les messages reçus et les transmet aux autres clients connectés.

### 5.2. Découverte automatique des serveurs avec UDP

Afin d'éviter à l'utilisateur de devoir connaître manuellement l'adresse IP et le port du serveur, un mécanisme de découverte automatique a été ajouté.

Le fonctionnement est le suivant :

1. Le client envoie une requête UDP de découverte sur le réseau local.
2. Le serveur écoute les requêtes sur le port UDP `59000`.
3. Lorsqu'il reçoit une requête valide, il répond en communiquant son nom et son port TCP.
4. Le client récupère les réponses et affiche les serveurs détectés dans l'interface graphique.

Ce mécanisme utilise le broadcast UDP pour rechercher les serveurs disponibles sur le réseau local.

**Important :** la découverte automatique fonctionne dans les conditions où les communications UDP broadcast sont autorisées sur le réseau. Elle n'est pas destinée à rechercher des serveurs sur Internet.

### 5.3. Gestion simultanée des clients

Le serveur utilise des threads pour gérer plusieurs clients indépendamment.

Chaque connexion est prise en charge par un thread dédié, ce qui permet au serveur de continuer à accepter de nouveaux clients pendant que les autres échangent des messages.

Un verrou (`threading.Lock`) protège également la liste partagée des clients afin d'éviter des modifications simultanées problématiques.

### 5.4. Interface graphique et gestion des threads

L'interface graphique est développée avec Tkinter.

Elle permet notamment :
- De saisir un pseudonyme.
- De rechercher les serveurs disponibles.
- De sélectionner un serveur.
- De se connecter et de se déconnecter.
- D'envoyer et de recevoir des messages.

Pour éviter les conflits entre les threads réseau et l'interface graphique, le programme utilise `queue.Queue()`.

Les événements reçus par les threads réseau sont placés dans une file d'attente. L'interface graphique les récupère ensuite depuis son propre thread principal grâce à la méthode `after()` de Tkinter.

Cette organisation permet de conserver une interface réactive pendant les communications réseau.

## 6. Gestion des erreurs et des déconnexions

Plusieurs vérifications ont été ajoutées pour améliorer la stabilité du programme :

- Gestion des erreurs lors de la connexion au serveur.
- Vérification de la réception des données.
- Détection de la déconnexion d'un client ou du serveur.
- Gestion des erreurs liées aux sockets.
- Gestion des erreurs de décodage des messages.
- Nettoyage des connexions et des ressources lors de la fermeture.

Ces améliorations permettent d'éviter certaines interruptions inattendues et de gérer plus proprement les déconnexions.

## 7. Utilisation sur plusieurs ordinateurs

Pour utiliser l'application entre plusieurs ordinateurs :

1. Les ordinateurs doivent être connectés au même réseau local.
2. Le serveur doit être lancé sur l'un des ordinateurs.
3. Les autres utilisateurs lancent le client graphique.
4. Ils recherchent les serveurs disponibles et sélectionnent celui auquel ils souhaitent se connecter.

Il faut également vérifier que le pare-feu autorise les communications sur les ports TCP `59001` et UDP `59000`.

Si la découverte automatique ne fonctionne pas, il est possible de vérifier les paramètres réseau et les autorisations du pare-feu.

## 8. Résumé des ports utilisés

| Protocole | Port | Utilisation |
|---|---:|---|
| TCP | 59001 | Communication et échange des messages entre clients et serveur. |
| UDP | 59000 | Découverte automatique des serveurs sur le réseau local. |

## 9. Conclusion

Ce projet permet de mettre en pratique plusieurs notions fondamentales de la programmation réseau en Python : les sockets TCP et UDP, la communication client-serveur, le multithreading et la synchronisation entre threads.

Les améliorations apportées permettent de passer d'une application principalement basée sur la console à une application disposant d'une interface graphique et d'un mécanisme de découverte automatique des serveurs.

Le projet constitue ainsi une mise en pratique de la communication réseau et de la programmation concurrente en Python.