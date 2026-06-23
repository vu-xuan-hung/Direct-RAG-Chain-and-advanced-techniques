from neo4j import GraphDatabase

driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "12345678"))
def print_nodes(tx):
    result = tx.run("MATCH (p:PolicyClause) RETURN p.title as title, p.text as text")
    for record in result:
        print(f"Title: {record['title']}")

with driver.session() as session:
    session.read_transaction(print_nodes)

driver.close()
