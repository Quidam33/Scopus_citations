from pybliometrics.scopus import AbstractRetrieval
import networkx as nx
from pymongo import MongoClient

client = MongoClient("mongodb+srv://new_user:1234@scopusdb.c3tpx.mongodb.net/scopus_v4?retryWrites=true&w=majority")
db = client.scopus_v4
article_collection = db.scopus_articles
G = nx.DiGraph()

articles = ["85085679806", "85104304072", "85097109605", "85101284824"]
closed_set = []
relations = []
documents = []


def insert_document(collection, data):
    return collection.insert_one(data).inserted_id


def get_article_ref(article, parent, level):
    if level < 3:
        if article is not None:
            if article not in closed_set:
                print(article)
                ab = AbstractRetrieval(article, view='FULL')
                data = {'parent_eid': parent, 'date': ab.coverDate, 'eid': ab.eid, 'authors': ab.authors,
                        'title': ab.title,
                        'abstract': ab.abstract, 'description': ab.description, 'keywords': ab.authkeywords,
                        'cites': ab.citedby_count}
                relations.append([article, parent, level])
                insert_document(article_collection, data)
                references = ab.references
                level += 1
                for obj in references or []:
                    if obj is None:
                        continue
                    if obj[1] is not None:
                        closed_set.append(article)
                        get_article_ref(obj[1], article, level)


try:
    for publication in articles:
        get_article_ref(publication, 0, 0)
except Exception:
    for obj in relations:
        if obj[2] < 2:
            get_article_ref(obj[0], obj[1], obj[2])

for doc in article_collection.find({}, {"_id": 0, "eid": 1, "parent_eid": 1}):
    documents.append([doc['parent_eid'], doc['eid'][7:]])

closed_set = []

for doc in documents:
    if doc[0] not in closed_set and doc[0] != 0:
        G.add_node(doc[0], date=doc[2])
        closed_set.append(doc[0])
    if doc[1] not in closed_set:
        G.add_node((doc[1]))
        closed_set.append(doc[1])
    if doc[0] != 0:
        G.add_edge(doc[0], doc[1])

nx.write_gml(G, "graph.gml")
