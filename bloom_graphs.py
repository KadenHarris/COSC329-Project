import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
 
from build_graph import load_edges
 
LEVELS = ["Remembering", "Understanding", "Applying", "Analyzing", "Evaluating", "Creating"]
COLORS = {
    "Remembering": "#0072B2", "Understanding": "#56B4E9", "Applying": "#009E73",
    "Analyzing": "#E69F00", "Evaluating": "#D55E00", "Creating": "#CC79A7",
}
RADS = dict(zip(LEVELS, [-0.35, -0.21, -0.07, 0.07, 0.21, 0.35]))
 
 
def draw_nodes(ax, M, pos, names, activity, scale, font):
    act = np.array([activity[u] for u in M.nodes])
    sizes = scale * (300 + 2700 * act / act.max())
    nx.draw_networkx_nodes(M, pos, node_size=sizes, node_color="#4C78A8",
                           edgecolors="white", linewidths=1.2, alpha=0.95, ax=ax)
    nx.draw_networkx_labels(M, pos, labels=names, font_size=font, ax=ax,
                            bbox=dict(boxstyle="round,pad=0.15", fc="white",
                                      ec="none", alpha=0.8))
    return sizes
 
 
def draw_level(ax, M, pos, level, sizes, max_count):
    edges = [(u, v) for u, v, k in M.edges(keys=True) if k == level]
    if not edges:
        return
    widths = [0.8 + 7 * M[u][v][level]["count"] / max_count for u, v in edges]
    nx.draw_networkx_edges(M, pos, edgelist=edges, width=widths,
                           edge_color=COLORS[level], alpha=0.8, arrows=True,
                           arrowstyle="-|>", arrowsize=14, node_size=sizes,
                           connectionstyle=f"arc3,rad={RADS[level]}", ax=ax)
 
 
def bloom_table(answers, bloom, ids):
    answers = answers.assign(bloom_level=answers["question_id"].map(bloom))
    among_top = answers[answers["answerer_id"].isin(ids) & answers["asker_id"].isin(ids)]
    classified = among_top[among_top["bloom_level"].isin(LEVELS)]
    table = (classified.groupby(["answerer_id", "asker_id", "bloom_level"])
             .size().reset_index(name="n_answers"))
    return table, len(among_top) - len(classified)
 
 
def main():
    q = pd.read_csv("data/questions.csv")
    a = pd.read_csv("data/answers.csv")
    bloom = pd.read_csv("data/questions_bloom.csv").set_index("question_id")["bloom_level"]
    nodes = pd.read_csv("output/top_nodes.csv")
    top_edges = pd.read_csv("output/top_edges.csv")
 
    _, answers = load_edges(q, a)
    ids = set(nodes["user_id"])
    table, excluded = bloom_table(answers, bloom, ids)
    if table.empty:
        print("No classified answers between the drawn users.")
        return
    table.rename(columns={"answerer_id": "source", "asker_id": "target",
                          "n_answers": "count"}).to_csv("output/bloom_edges.csv", index=False)
 
    names = dict(zip(nodes["user_id"], nodes["name"].astype(str)))
    activity = dict(zip(nodes["user_id"], nodes["activity"]))
 
    base = nx.DiGraph()
    base.add_nodes_from(ids)
    for r in top_edges.itertuples():
        base.add_edge(r.source, r.target, weight=int(r.weight))
    pos = nx.spring_layout(base, k=4.0 / np.sqrt(len(ids)), seed=42, iterations=300)
 
    M = nx.MultiDiGraph()
    M.add_nodes_from(ids)
    for r in table.itertuples():
        M.add_edge(r.answerer_id, r.asker_id, key=r.bloom_level, count=int(r.n_answers))
    max_count = table["n_answers"].max()
 
    fig, ax = plt.subplots(figsize=(13, 10))
    sizes = draw_nodes(ax, M, pos, names, activity, 1.0, 8)
    for level in LEVELS:
        draw_level(ax, M, pos, level, sizes, max_count)
    ax.legend(handles=[Line2D([0], [0], color=COLORS[l], lw=3, label=l) for l in LEVELS],
              loc="lower right", title="Bloom's level")
    ax.set_title("StackOverflow knowledge network by Bloom's level", fontsize=14)
    ax.text(0.01, 0.01,
            "Arrow: answerer -> asker.  Node size: questions asked + answers given.  "
            "Edge thickness: questions answered at that level.",
            transform=ax.transAxes, fontsize=9, color="#444")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig("output/bloom_graph.png", dpi=200)
    plt.close(fig)
 
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    for ax, level in zip(axes.flat, LEVELS):
        sizes = draw_nodes(ax, M, pos, names, activity, 0.35, 6)
        draw_level(ax, M, pos, level, sizes, max_count)
        part = table[table["bloom_level"] == level]
        ax.set_title(f"{level}: {len(part)} pairs, {part['n_answers'].sum()} answers",
                     fontsize=12, color=COLORS[level])
        ax.axis("off")
    fig.tight_layout()
    fig.savefig("output/bloom_levels.png", dpi=200)
    plt.close(fig)
 
    summary = (table.groupby("bloom_level")["n_answers"]
               .agg(pairs="size", answers="sum").reindex(LEVELS).fillna(0).astype(int))
    print(summary.to_string())
    print(f"\nExcluded {excluded} answers between these users (question has no Bloom's level)")
    print("\nTop answerer per level (among the drawn users):")
    for level in LEVELS:
        s = (table[table["bloom_level"] == level].groupby("answerer_id")["n_answers"]
             .sum().sort_values(ascending=False))
        if len(s):
            print(f"  {level}: {names[s.index[0]]} ({s.iloc[0]} answers)")
    print("\nSaved output/bloom_graph.png, output/bloom_levels.png, output/bloom_edges.csv")
 
 
if __name__ == "__main__":
    main()
 