import networkx as nx
import pandas as pd
 
from build_graph import load_edges
 
 
def compute_centrality(edges):
    G = nx.DiGraph()
    for r in edges.itertuples():
        G.add_edge(r.answerer_id, r.asker_id, weight=int(r.weight))
 
    hubs, auths = nx.hits(G, max_iter=1000)
    return pd.DataFrame({
        "in_degree": nx.in_degree_centrality(G),
        "out_degree": nx.out_degree_centrality(G),
        "hub": hubs,
        "authority": auths,
    })
 
 
def main():
    q = pd.read_csv("data/questions.csv")
    a = pd.read_csv("data/answers.csv")
    edges, _ = load_edges(q, a)
    scores = compute_centrality(edges)
 
    top_nodes = pd.read_csv("output/top_nodes.csv")
    df = top_nodes[["user_id", "name", "questions_asked", "answers_given"]].join(
        scores, on="user_id").sort_values("out_degree", ascending=False)
    df.to_csv("output/centrality.csv", index=False)
 
    print(f"Full network: {len(scores)} users, {len(edges)} edges")
    print(df.round(4).to_string(index=False))
 
 
if __name__ == "__main__":
    main()
 