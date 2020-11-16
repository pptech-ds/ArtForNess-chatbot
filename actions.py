# -*- coding: utf-8 -*-
import csv
import random
import logging
import requests
import numpy as np
from tqdm import tqdm
from typing import Text, Dict, Any, List
import re

from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.forms import FormAction
from rasa_sdk.events import SlotSet, UserUtteranceReverted, ConversationPaused, FollowupAction

from modules.bm25 import bm25_scoring

from modules.functions import build_keywords_list

logger = logging.getLogger(__name__)

# déclare les paramètres de l'IR dans un dict
arg_dict = {}
arg_dict['max_seq_length'] = 512
arg_dict['per_gpu_eval_batch_size'] = 32
arg_dict['es_nb_max_result'] = 3
arg_dict['tolerance'] = 0.01
arg_dict['language'] = 'french'
arg_dict['device'] = 'cpu'
arg_dict['stopwords_csv'] = 'data_ir/stopwords.csv'
arg_dict['artistes_csv'] = 'data_ir/artforness_data_artistes.csv'
arg_dict['oeuvres_csv'] = 'data_ir/artforness_data_oeuvres.csv'

# Setup logging
logging.basicConfig(format = '%(asctime)s - %(levelname)s - %(name)s -   %(message)s',
                    datefmt = '%m/%d/%Y %H:%M:%S',
                    level = logging.INFO)
logger.warning("Process rank: %s, device: %s, distributed training: %s, 16-bits training: %s",
                -1, arg_dict['device'], bool(-1 != -1), '')


class ActionRechercher(Action):
    """ Fonction custom de recherche dans la base par l'intervention de deux modèles :
            - récupère l'input de l'utilisateur,
            - procède à un filtrage verbes-noms par spaCy,
            - requête le modèle d'Information Retrieving (IR) qui identifie les sources de réponse,
            - complété par le modèle de Reranking (Reranker) qui vérifie la pertinence des sources,
            - identifie les n premières propositions de réponse par un seuil de tolérance,
            - renvoie le résultat de la recherche à l'utilisateur.
    """

    def name(self):
        return "action_rechercher"

    def run(self, dispatcher, tracker, domain):
        # récupère l'intent et la requête du dernier message utilisateur
        intent = tracker.latest_message['intent'].get('name')
        query = (tracker.latest_message)['text']

        # ainsi que la valeur du slot booléen "relance"
        relance = tracker.get_slot("relance")
        
        # teste la valeur de l'intent ou du slot "relance"
        if intent == "recherche" or relance == True:

            bm25_result = bm25_scoring(arg_dict['oeuvres_csv'], query)
            print('actions.py: oeuvres_csv: {}'.format(arg_dict['oeuvres_csv']))
            print('actions.py: query: {}'.format(query))
            print('actions.py: len(bm25_result): {}'.format(len(bm25_result)))

            # teste si outputs non vides
            if(len(bm25_result) > 0):
                # print debug classifier
                for i in range(len(bm25_result)):
                    print('bm25_result.iloc[{}][Titre]: {} / bm25_result.iloc[{}][Lien]: {} / bm25_result.iloc[{}][score]: {}\n'.format(i, bm25_result.iloc[i]['Titre'], i, bm25_result.iloc[i]['Lien'], i, bm25_result.iloc[i]['score']))

                # en déclarant les messages de retours qui seront sélectionnés au hasard
                retour = [
                    "Voilà ce que j'ai trouvé :",
                    "Voici quelques éléments de réponse :",
                    "Quelques pistes de réflexion :",
                    "Hop ! A toi de chercher là-dedans maintenant :"
                ]

                # # en les concaténant tous dans un même message
                # message = random.choice(retour)
                # message = message + '\n TEST PRAS'
                # dispatcher.utter_message(message)

                # en les concaténant tous dans un même message
                message = '\"' + random.choice(retour) + '\"'
                for i in range(min(len(bm25_result), arg_dict['es_nb_max_result'])):
                    current_titre = bm25_result.iloc[i]['Titre'].replace('\"', '')
                    current_lien = bm25_result.iloc[i]['Lien'].replace('\"', '')
                    current_lien = re.sub('\s+', '', current_lien)
                    message = message + ' \"{}\" \"{}\" '.format(
                            current_titre,
                            current_lien
                            )
                dispatcher.utter_message(message)
                print('message: {}'.format(message))

                # puis retourne le slot "recherche" à "reussie",
                # et retourne le slot "relance" à "False"
                return [
                    SlotSet("recherche", "reussie"),
                    SlotSet("relance", False),
                    UserUtteranceReverted()
                    ]

            else:
                # si non, renvoie un message d'échec
                dispatcher.utter_message("utter_recherche_echouee", tracker)

                # puis retourne le slot "recherche" à "echouee",
                # et retourne le slot "relance" à "False"
                return [
                    SlotSet("recherche", "echouee"),
                    SlotSet("relance", False),
                    UserUtteranceReverted()
                    ]
           
        
        # sinon retourne un message d'erreur (méthode "Raise" n'atteint pas l'utilisateur)
        else:
            return dispatcher.utter_message('Ah, j\'ai rencontré un problème système, je ne parviens pas à lancer ta recherche, essaie de la reformuler mais si le problème persiste, contacte un référent et transmet-lui le message suivant afin qu\'il me répare s\'il-te-plaît : "Erreur : intent >< \'recherche\' ET slot \'relance\' = False"')


class ActionDefaultFallback(Action):
    """ Fonction custom de fallback par défaut matérialisée par l'incompréhension du chatbot :
            - annule la dernière incompréhension pour ne pas impacter les prédictions futures,
            - force une action de recherche par défaut.
    """

    def name(self) -> Text:
        return "action_incomprehension"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List["Event"]:

        # retourne un message d'incompréhension à l'utilisateur indiquant le lancement d'une recherche par défaut
        dispatcher.utter_template("utter_incomprehension", tracker),

        # puis retourne le slot booléen "relance" à "True" 
        # et lance la fonction de recherche
        return [
            SlotSet("relance", True),
            FollowupAction("action_rechercher"),
            ]


class Conversation(Action):
    """Retourne le utter correspondant à l'intent conversationnel détecté."""

    def name(self):
        return "action_conversation"

    def run(self, dispatcher, tracker, domain):
        intent = tracker.latest_message["intent"].get("name")

        # récupère l'utter conversationnel correspondant à l'intent détecté
        if intent in [
            "saluer",
            "identite", 
            "insulter",
            "createur",
            "meteo",
            "possibilites",
            "isbot",
            "quel_age",
            "quelle_langue",
            "quelle_heure",
            "qui_suis_je",
            "quel_nom",
            "origine_lieu",
            "origine_construction",
            "faire_connaissance",
            "faire_blague",
            "quel_genre",
            "merci",
            "affirmer",
            "infirmer",
            "complimenter"
        ]:
            dispatcher.utter_template("utter_" + intent, tracker)
        return []