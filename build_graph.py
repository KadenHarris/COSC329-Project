import argparse
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd


def load_edges(q, a):
    m = a.merge(q[["question_id", "asker_id"]], on="question_id")
    m = m[m["answerer_id"] != m["asker_id"]]
    edges = m.groupby(["answerer_id", "asker_id"]).size().reset_index(name="weight")
    return edges, m


def user_activity(q, answers):
    asked = q.groupby("asker_id").size().rename("questions_asked")
    given = answers.groupby("answerer_id").size().rename("answers_given")
    act = pd.concat([asked, given], axis=1).fillna(0).astype(int)
    act["activity"] = act["questions_asked"] + act["answers_given"]
    act.index.name = "user_id"
    return act


def user_names(q, a):
    names = pd.concat([q.set_index("asker_id")["asker_name"],
                       a.set_index("answerer_id")["answerer_name"]])
    return names[~names.index.duplicated()].to_dict()


def select_users(edges, activity, top):
    ranked = edges.assign(
        pair_activity=edges["answerer_id"].map(activity["activity"])
        + edges["asker_id"].map(activity["activity"])
    ).sort_values(["weight", "pair_activity"], ascending=False)

    selected = set()
    for r in ranked.itertuples():
        new = {r.answerer_id, r.asker_id} - selected
        if len(selected) + len(new) <= top:
            selected |= new
        if len(selected) >= top:
            break
    return selected


def draw(G, activity, out_png):
    n = G.number_of_nodes()
    pos = nx.spring_layout(G, k=4.0 / np.sqrt(max(n, 1)), seed=42, iterations=300)

    act = np.array([activity.loc[u, "activity"] for u in G.nodes])
    node_sizes = 300 + 2700 * act / act.max()

    weights = np.array([d["weight"] for _, _, d in G.edges(data=True)])
    widths = 0.8 + 7 * weights / weights.max()

    fig, ax = plt.subplots(figsize=(13, 10))
    nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color="#4C78A8",
                           edgecolors="white", linewidths=1.5, alpha=0.95, ax=ax)
    nx.draw_networkx_edges(G, pos, width=widths, edge_color="#7a7a7a", alpha=0.65,
                           arrows=True, arrowstyle="-|>", arrowsize=16,
                           node_size=node_sizes, connectionstyle="arc3,rad=0.15", ax=ax)
    nx.draw_networkx_labels(G, pos, labels=nx.get_node_attributes(G, "name"),
                            font_size=8, ax=ax,
                            bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                      ec="none", alpha=0.8))
    ax.set_title(f"StackOverflow knowledge network ({n} users, strongest answerer-asker pairs)",
                 fontsize=14)
    ax.text(0.01, 0.01,
            "Arrow: answerer -> asker.  Node size: questions asked + answers given.  "
            "Edge thickness: questions answered.",
            transform=ax.transAxes, fontsize=9, color="#444")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(out_png, dpi=200)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=20)
    args = ap.parse_args()

    os.makedirs("output", exist_ok=True)
    q = pd.read_csv("data/questions.csv")
    a = pd.read_csv("data/answers.csv")

    edges, answers = load_edges(q, a)
    activity = user_activity(q, answers)
    names = user_names(q, a)

    top_ids = select_users(edges, activity, args.top)
    top_edges = edges[edges["answerer_id"].isin(top_ids) & edges["asker_id"].isin(top_ids)]

    G = nx.DiGraph()
    for uid in top_ids:
        G.add_node(uid, name=str(names.get(uid, uid)))
    for r in top_edges.itertuples():
        G.add_edge(r.answerer_id, r.asker_id, weight=int(r.weight))

    print(f"Full network: {len(activity)} users, {len(edges)} directed pairs")
    print(f"Drawn graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

    nodes_df = pd.DataFrame(
        [{"user_id": u, "name": G.nodes[u]["name"], **activity.loc[u].to_dict()}
         for u in G.nodes]).sort_values("activity", ascending=False)
    nodes_df.to_csv("output/top_nodes.csv", index=False)
    top_edges.rename(columns={"answerer_id": "source", "asker_id": "target"}) \
             .to_csv("output/top_edges.csv", index=False)

    draw(G, activity, "output/original_graph.png")
    print("Saved figure and tables to output/")


if __name__ == "__main__":
    main()