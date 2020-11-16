## demarrer
* demarrer
    - utter_demarrer
    
## bonjour
* bonjour
    - utter_bonjour

## aurevoir
* aurevoir
    - utter_aurevoir

## scena1
* bonjour
    - utter_bonjour
* recherche
    - utter_recherche
    - action_rechercher{"recherche":"reussie"}
    - slot{"recherche":"reussie"}
    - slot{"relance":"false"}
* aurevoir
    - utter_aurevoir

## trouver
* recherche
    - utter_recherche
    - action_rechercher{"recherche":"reussie"}
    - slot{"recherche":"reussie"}
    - slot{"relance":"false"}

## ne pas trouver
* recherche
    - utter_recherche
    - action_rechercher{"recherche":"echouee"}
    - slot{"recherche":"echouee"}
    - slot{"relance":"false"}

## conversation
* saluer OR identite OR insulter OR createur OR possibilites OR isbot OR quel_age OR quelle_langue OR quelle_heure OR qui_suis_je OR quel_nom OR origine_lieu OR origine_construction OR faire_connaissance OR faire_blague OR quel_genre OR merci OR affirmer OR infirmer OR complimenter
    - action_conversation

