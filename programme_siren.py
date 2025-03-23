import requests
import time
import pandas as pd
import os
import re
from bs4 import BeautifulSoup


repertoire = "/Users/julie/Downloads/étude/Recherche: stage/csv"
url = 'https://www.data.gouv.fr/fr/datasets/'


def fichier_dataset(url):
    liste_nom_dataset = []
    for i in range(1, 2):
        url_page = f"https://www.data.gouv.fr/fr/datasets/?page={i}"
        response = requests.get(url_page)
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = soup.find_all('article', class_='fr-my-3w fr-p-3w border border-default-grey fr-enlarge-link')
        for article in articles:
            nom_dataset = article.find('h4').find('a').text.strip().replace('\n', '').lower()
            nom_dataset = re.sub(r'[^a-z0-9\s]', '', nom_dataset)
            nom_dataset = re.sub(r'\s+', '-', nom_dataset)
            print(nom_dataset)
            liste_nom_dataset.append(nom_dataset)
    return liste_nom_dataset



def telecharger_fichier(url, repertoire_local, nom_local, taille_max_octets=100000000):
    try:
        response = requests.head(url)
        if response.status_code == 200:
            taille_fichier = int(response.headers.get('content-length', 0))
            if taille_fichier <= taille_max_octets:
                print(f"Téléchargement du fichier depuis {url} vers {os.path.join(repertoire_local, nom_local)}")
                response = requests.get(url)
                chemin_fichier_local = os.path.join(repertoire_local, nom_local)
                with open(chemin_fichier_local, 'wb') as fichier_local:
                    fichier_local.write(response.content)
            else:
                print("Ignorer le fichier. La taille du fichier est trop grande.")
        else:
            print(f"Ignorer le fichier. La requête a échoué avec le code de statut : {response.status_code}")
    except requests.RequestException as e:
        print(f"Une erreur s'est produite lors du téléchargement du fichier. Erreur : {str(e)}")
        
        

def numero_potentielle(fichier):
    siren_liste = []
    siret_liste = []
    try:
        df = pd.read_csv(os.path.join(repertoire, fichier), delimiter=';', nrows=30, encoding='latin1')
        for colonne in df.columns:
            for valeur in df[colonne].astype(str):
                valeur = valeur.replace(' ', '')
                if valeur.isdigit() and len(valeur) == 9 and valeur not in siren_liste:
                    siren_liste.append(valeur)
                elif valeur.isdigit() and len(valeur) == 14 and valeur not in siret_liste:
                    siret_liste.append(valeur)
    except pd.errors.ParserError as e:
        print(f"Il n'y a pas de numéro SIREN/SIRET. Le fichier {fichier} sera ignoré.")
    return siren_liste, siret_liste


def numero_potentielle_par_fichier(repertoire):
    numeros_par_fichier = {}
    for fichier in os.listdir(repertoire):
        numeros_par_fichier[fichier] = numero_potentielle(fichier)
    return numeros_par_fichier



url_base_sirene = "https://api.insee.fr/entreprises/sirene/V3/siren/" #la fin (qui suit siren/) correspondra au numéro siren que l'on souhaite interroger
url_base_sret = "https://api.insee.fr/entreprises/sirene/V3/siret/" #+la fin un numéro siret


# cURL API: curl -X GET --header 'Accept: application/json' --header 'Authorization: Bearer 1e3d323f-299b-350d-8991-ba479c31ff0a' 

headers = {
    "Accept": "application/json",
    "Authorization": "Bearer 7c8899f4-b421-3bcd-9106-ff530fef701e" 
    }


def verifier_numero(liste_siren, liste_siret):
    for siren in liste_siren:
        print("Numéro SIREN:", siren)
        url = f"{url_base_sirene}{siren}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(response.json())
            else:
                print("Code de statut:", response.status_code)
                print("Contenu:", response.text)
            time.sleep(3)
        except requests.exceptions.RequestException as e:
            print(f"Une erreur s'est produite lors de la requête pour le numéro SIREN {siren} :", str(e))

    for siret in liste_siret:
        print("Numéro SIRET:", siret)
        url = f"{url_base_sret}{siret}"
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                print(response.json())
            else:
                print("Code de statut:", response.status_code)
                print("Contenu:", response.text)
            time.sleep(3)
        except requests.exceptions.RequestException as e:
            print(f"Une erreur s'est produite lors de la requête pour le numéro SIRET {siret} :", str(e))



def supprimer_doublons(repertoire):
    fichiers = {}
    for element in os.listdir(repertoire):
        chemin_element = os.path.join(repertoire, element)
        if os.path.isdir(chemin_element):
            for nom_fichier in os.listdir(chemin_element):
                chemin_fichier = os.path.join(chemin_element, nom_fichier)
                if nom_fichier in fichiers:
                    os.remove(chemin_fichier)
                    print(f"Le fichier en double {nom_fichier} a été supprimé.")
                else:
                    fichiers[nom_fichier] = chemin_fichier
    print("Les fichiers en double ont été supprimés.")
    



liste_nom_dataset = fichier_dataset(url)
for fichier in liste_nom_dataset:
    url_fichier = f"https://www.data.gouv.fr/fr/datasets/{fichier}/"
    nom_fichier_local = f"{fichier}.csv"
    telecharger_fichier(url_fichier, repertoire, nom_fichier_local)

numeros_par_fichier = numero_potentielle_par_fichier(repertoire)

for fichier, numeros in numeros_par_fichier.items():
    print(f"Numéros SIREN détectés dans le fichier {fichier} :", numeros[0])
    print(f"Numéros SIRET détectés dans le fichier {fichier} :", numeros[1])

sirens = [num for sublist in [numeros[0] for numeros in numeros_par_fichier.values()] for num in sublist]
sirets = [num for sublist in [numeros[1] for numeros in numeros_par_fichier.values()] for num in sublist]

supprimer_doublons(repertoire)







