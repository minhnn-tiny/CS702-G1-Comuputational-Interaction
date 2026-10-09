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
        c.attr(label="schools  j ∈ {GP, MS}", **{**PLATE, "labelloc": "t"})
        c.node("a_s", "<a<SUB>j</SUB>>")
        c.node("pad_s", "", shape="box", style="invis", width="0.85", height="0.3", fixedsize="true")
    with g.subgraph(name="cluster_mjob") as c:
        c.attr(label="mother's job  m = 1, …, 5", **{**PLATE, "labelloc": "t"})
        c.node("pad_m", "", shape="box", style="invis", width="1.1", height="0.3", fixedsize="true")
        c.node("a_m", "<b<SUB>m</SUB>>")
    with g.subgraph(name="cluster_students") as c:
        c.attr(label="students  i = 1, …, 395", **PLATE)
        c.node("x", "<x<SUB>i</SUB>>", **OBS)
        c.node("mu", "<&mu;<SUB>i</SUB>>", **DET)
        c.node("G3", "<G3<SUB>i</SUB>>", **OBS)
        c.edge("x", "mu")
        c.edge("mu", "G3")
    # group scales sit beside their plates (minlen=0: same row), so no arrow
    # crosses a plate label
    g.edge("ss", "a_s", minlen="0")
    g.edge("a_m", "sm", minlen="0", dir="back")  # laid out left to right, arrow points at b_m
    g.edge("a_s", "mu")
    g.edge("a_m", "mu")
    g.edge("alpha", "mu")
    g.edge("beta", "mu")
    g.edge("sigma", "G3")
    # group plates on the row above the student plate instead of beside it
    g.edge("a_s", "x", style="invis")
    g.edge("a_m", "x", style="invis")
    # left-to-right order of the top row: sigma, sigma_sch -> a_j, b_m <- sigma_job, beta, alpha.
    # The invisible pads make each group plate as wide as its label, otherwise
    # the label widens the plate after layout and the two plates touch.
    for tail, head in [("sigma", "ss"), ("a_s", "pad_s"), ("pad_s", "pad_m"), ("pad_m", "a_m"),
                       ("sm", "beta"), ("beta", "alpha")]:
        g.edge(tail, head, style="invis", minlen="0")
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
