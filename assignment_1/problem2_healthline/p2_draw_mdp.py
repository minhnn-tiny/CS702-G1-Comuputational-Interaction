"""Problem 2, Q1.a -- node-edge diagram of the HealthLine MDP (Graphviz).

Conventions: states are circles (terminal states double circles, the initial
state has an incoming arrow); black squares are branching points where the
outcome of an action is probabilistic; edges are labelled with action names
(state -> square) and transition probabilities (square -> next state).
Actions with a single, certain outcome are drawn as one labelled edge.

Produces outputs/fig_mdp.pdf (+ .png).
"""

from __future__ import annotations

import graphviz

from healthline_mdp import INITIAL, OUT_DIR, STATE_NAMES, TERMINAL, TRANSITIONS

SHORT = {
    0: "initial", 1: "acute\ntrack", 2: "general\ntrack", 3: "admin\ntrack",
    4: "warning\nsigns", 5: "no warning\nsigns", 6: "info\ndelivered",
    7: "resolved", 8: "escalated\nnurse", 9: "escalated\nadmin", 10: "emergency", 11: "abandoned",
}


def build() -> graphviz.Digraph:
    g = graphviz.Digraph("fig_mdp", format="pdf")
    g.attr(rankdir="LR", nodesep="0.16", ranksep="0.5", margin="0.02", splines="true", dpi="300")
    g.attr("node", fontname="Helvetica", fontsize="9", width="0.74", height="0.74", fixedsize="true", penwidth="0.9")
    g.attr("edge", fontname="Helvetica", fontsize="7", arrowsize="0.55", penwidth="0.7", fontcolor="#333333")

    # initial-state arrow
    g.node("start", label="", shape="none", width="0.05", height="0.05")
    for s in sorted(STATE_NAMES):
        shape = "doublecircle" if s in TERMINAL else "circle"
        fill = {"style": "filled", "fillcolor": "#eeeeee"} if s == 11 else {}
        g.node(f"s{s}", label=f"<<I>s</I><SUB>{s}</SUB><BR/><FONT POINT-SIZE=\"7\">{SHORT[s].replace(chr(10), '<BR/>')}</FONT>>",
               shape=shape, **fill)
    g.edge("start", f"s{INITIAL}")

    for (s, a), P in TRANSITIONS.items():
        if len(P) == 1:  # deterministic action: direct edge
            (sn, p), = P.items()
            g.edge(f"s{s}", f"s{sn}", label=f"{a}\n{p:.2f}")
            continue
        b = f"b_{s}_{a}"
        g.node(b, label="", shape="square", style="filled", fillcolor="black", width="0.11", height="0.11")
        g.edge(f"s{s}", b, label=a, arrowhead="none")
        for sn, p in P.items():
            g.edge(b, f"s{sn}", label=f"{p:.2f}")

    # keep terminal states in one column
    with g.subgraph() as sg:
        sg.attr(rank="same")
        for t in TERMINAL:
            sg.node(f"s{t}")
    return g


if __name__ == "__main__":
    g = build()
    g.render(OUT_DIR / "fig_mdp", cleanup=True)
    g.format = "png"
    g.render(OUT_DIR / "fig_mdp", cleanup=True)
    print("wrote", OUT_DIR / "fig_mdp.pdf")
