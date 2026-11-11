import networkx as nx
import pandas as pd

from build_graph import load_edges


def main():
    q = pd.read_csv("data/questions.csv")
    a = pd.read_csv("data/answers.csv")
    edges, _ = load_edges(q, a)

    G = nx.DiGraph()
    for r in edges.itertuples():
        G.add_edge(r.answerer_id, r.asker_id, weight=int(r.weight))

    in_c = nx.in_degree_centrality(G)
    out_c = nx.out_degree_centrality(G)
    hubs, auths = nx.hits(G, max_iter=1000)

    top_nodes = pd.read_csv("output/top_nodes.csv")
    rows = [{
        "user_id": r.user_id,
        "name": r.name,
        "questions_asked": r.questions_asked,
        "answers_given": r.answers_given,
        "in_degree": in_c[r.user_id],
        "out_degree": out_c[r.user_id],
        "hub": hubs[r.user_id],
        "authority": auths[r.user_id],
    } for r in top_nodes.itertuples()]

    df = pd.DataFrame(rows).sort_values("out_degree", ascending=False)
    df.to_csv("output/centrality.csv", index=False)

    print(f"Full network: {G.number_of_nodes()} users, {G.number_of_edges()} edges")
    print(df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()