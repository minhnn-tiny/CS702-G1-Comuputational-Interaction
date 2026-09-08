"""Problem 1, Q1.b -- plate diagrams of the two models (Graphviz).

Conventions (Lee & Wagenmakers, 2013): circles are continuous variables,
shaded nodes are observed, unshaded nodes are latent, a dashed border marks a
deterministic node, and plates (rectangles) denote replication.

Produces outputs/plate_m1.pdf and outputs/plate_m2.pdf (plus .png).
"""

from __future__ import annotations

from pathlib import Path

import graphviz

OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

NODE = dict(shape="circle", fontname="Helvetica", fontsize="11", width="0.42", fixedsize="true", penwidth="0.8")
OBS = dict(style="filled", fillcolor="#d3d3d3")
DET = dict(style="dashed")
EDGE = dict(arrowsize="0.6", penwidth="0.7")
PLATE = dict(fontname="Helvetica", fontsize="9", labelloc="b", labeljust="r", penwidth="0.8", color="#444444")


def base(name):
    g = graphviz.Digraph(name, format="pdf")
    g.attr(rankdir="TB", nodesep="0.25", ranksep="0.32", margin="0.02", dpi="300")
    g.attr("node", **NODE)
    g.attr("edge", **EDGE)
    return g


def model1():
    g = base("plate_m1")
    g.node("alpha", "<&alpha;>")
    g.node("beta", "<&beta;>")
    g.node("sigma", "<&sigma;>")
    with g.subgraph(name="cluster_students") as c:
        c.attr(label="students  i = 1, …, 395", **PLATE)
        c.node("x", "<x<SUB>i</SUB>>", **OBS)
        c.node("mu", "<&mu;<SUB>i</SUB>>", **DET)
        c.node("G3", "<G3<SUB>i</SUB>>", **OBS)
        c.edge("x", "mu")
        c.edge("mu", "G3")
    g.edge("alpha", "mu")
    g.edge("beta", "mu")
    g.edge("sigma", "G3")
    return g


def model2():
    g = base("plate_m2")
    g.node("alpha", "<&alpha;>")
    g.node("beta", "<&beta;>")
    g.node("sigma", "<&sigma;>")
    g.node("ss", "<&sigma;<SUB>sch</SUB>>")
    g.node("sm", "<&sigma;<SUB>job</SUB>>")
    with g.subgraph(name="cluster_school") as c:
        c.attr(label="schools  j ∈ {GP, MS}", **PLATE)
        c.node("a_s", "<a<SUB>j</SUB>>")
    with g.subgraph(name="cluster_mjob") as c:
        c.attr(label="mother's job  m = 1, …, 5", **PLATE)
        c.node("a_m", "<b<SUB>m</SUB>>")
    with g.subgraph(name="cluster_students") as c:
        c.attr(label="students  i = 1, …, 395", **PLATE)
        c.node("x", "<x<SUB>i</SUB>>", **OBS)
        c.node("mu", "<&mu;<SUB>i</SUB>>", **DET)
        c.node("G3", "<G3<SUB>i</SUB>>", **OBS)
        c.edge("x", "mu")
        c.edge("mu", "G3")
    g.edge("ss", "a_s")
    g.edge("sm", "a_m")
    g.edge("a_s", "mu")
    g.edge("a_m", "mu")
    g.edge("alpha", "mu")
    g.edge("beta", "mu")
    g.edge("sigma", "G3")
    # keep hyper-parameters on one row
    with g.subgraph() as s:
        s.attr(rank="same")
        s.node("ss")
        s.node("sm")
        s.node("alpha")
        s.node("beta")
        s.node("sigma")
    return g


if __name__ == "__main__":
    for g in (model1(), model2()):
        g.render(OUT_DIR / g.name, cleanup=True)
        g.format = "png"
        g.render(OUT_DIR / g.name, cleanup=True)
        print("wrote", OUT_DIR / f"{g.name}.pdf")
