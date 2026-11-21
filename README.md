# PROJET-DONNEES-MASSIVES-ET-CLOUD
> TinyInsta passe-t-elle à l’échelle ? — Benchmark, édition 2026

<!--
Sections imposées du README : 
1. Montage (projet, région, versions, dates, d’où tourne le client).
2. Résultats des parties 1 à 3 (pour chacune : hypothèse, figures, interprétation).
3. Tableau des verdicts.
4. Validité.
5. Coût de la campagne.
-->

# Journal de bord

## 1. Montage
- Projet : tp1bigdata2026
- Région : europe-west1
- Versions :
    - Par défaut en autoscaling 20261121t111034, créée le 21/11 à 12h12m38s (2026-11-21T11:12:38+00:00) avec l'URL https://tp1bigdata2026.ew.r.appspot.com <!-- J'ai repris la base du projet TP1 -->
    - fixed1 : 1 instance fixe (sans autoscaling), créée le 21/11 à 15h39m55s (2026-11-21T14:39:55+00:00) avec l'URL : https://fixed1-dot-tp1bigdata2026.ew.r.appspot.com
- Client : Locust 2.47.0, lancé depuis Cloud Shell

## 2. Résultats
### Partie 1 — Coût d’une requête  

> Question : de quoi dépend le temps de traitement d’une timeline ?

- Analyse de la fonction get_timeline dans le main.py :
    - La fonction a pour but d'envoyer 20 posts des gens que l'utilisateur suit et les posts de l'utilisateur lui-même dans son fil d'actualité (timeline)
    - Elle est composée de 3 méthodes d'obtenir cette timeline :
        1. Première méthode : Utilise GQL si le SDK python est capable pour obtenir les 20 derniers posts des utilisateurs suivis par date de création, sinon appelle deuxième méthode. À noter qu'après un test effectué plus tard dans le développement, j'ai testé si la bibliothèque "google-cloud-datastore" possédait la méthode "gql" et le résultat est non. 
        Voir requête ci-dessous :
        ```> victorfombertasse@cloudshell:~ (tp1bigdata2026)$ python3 -c "from google.cloud import datastore; print('gql ?', hasattr(datastore.Client(), 'gql'))"
        > gql ? False```
        2. Deuxième méthode : Possède le même sens que la requête d'avant, mais construite avec des fonctions python. À noter que le paramètre 'IN' ne peut excéder 30 clauses d'égalité (==) sur la même propriété. [Utilisez l'opérateur `IN` pour combiner jusqu'à 30 clauses d'égalité (`==`) sur la même propriété avec un opérateur `OR` logique.](https://docs.cloud.google.com/datastore/docs/concepts/queries?hl=fr#in)
        3. Troisième méthode : Possède aussi le même sens que les requêtes d'avant. Cette méthode effectue manuellement les égalités en faisant une requête pour chacun des gens que l'on suit (peut devenir très couteux si l'on suit beaucoup de gens).

- Hypothèse pour chaque attribut :
    - U : Qu'il y ait 1 ou énormément d'utilisateurs la requête s'effectue juste pour 1 utilisateur, donc le temps de traitement devrait être quasi constant.
    - P : Dû au limit 20 et avec l'index trié par date, on ne lit jamais plus de 20 posts par requête, donc le temps de traitement devrait être quasi constant.
    - F : La liste envoyée au 'IN' contient F+1 valeurs (les F gens suivis + l'utilisateur lui-même).
        - Si F+1 ≤ 30, soit F ≤ 29 : deuxième méthode, une seule requête, donc temps de traitement quasi constant.
        - Si F+1 > 30, soit F ≥ 30 : la limite de 30 du 'IN' fait échouer la deuxième méthode, et ça bascule sur la troisième, qui fait F+1 requêtes les unes après les autres. Le temps de traitement devrait alors être linéaire en F.
        - On s'attend donc à voir un goulot d'étranglement à F = 30.

### Partie 2
### Partie 3

## 3. Verdicts

## 4. Validité 

## 5. Coût de la campagne 