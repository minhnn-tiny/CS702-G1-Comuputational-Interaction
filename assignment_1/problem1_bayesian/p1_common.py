"""Problem 1 -- shared data preparation and NumPyro model definitions.

Two Bayesian models of the final mathematics grade ``G3`` (0-20) from the UCI
Student Performance data set (``student-mat.csv``).  ``G1`` and ``G2`` are
never used.

Model 1 (H1, complete pooling)
    G3_i ~ Normal(mu_i, sigma),  mu_i = alpha + x_i . beta
    Individual behaviour / background predictors only; one common set of
    coefficients for every student.

Model 2 (H2, partial pooling / hierarchical)
    G3_i ~ Normal(mu_i, sigma),
    mu_i = alpha + a_school[school_i] + a_mjob[mjob_i] + x_i . beta
    a_school[j] ~ Normal(0, sigma_school),  a_mjob[m] ~ Normal(0, sigma_mjob)
    Varying intercepts for the two schools and the five maternal-occupation
    groups, with the group-level standard deviations learned from the data
    (non-centred parameterisation for sampling efficiency).
"""

from __future__ import annotations

import os
from pathlib import Path

import jax.numpy as jnp
import numpy as np
import numpyro
import numpyro.distributions as dist
import pandas as pd

HERE = Path(__file__).resolve().parent
DATA_PATH = HERE / "data" / "student-mat.csv"
OUT_DIR = HERE / "outputs"
OUT_DIR.mkdir(exist_ok=True)

# Individual-level predictors used by both models (in this order).
FEATURES = ["failures", "absences_log", "studytime", "higher", "goout", "Medu"]
FEATURE_LABELS = {
    "failures": "past failures",
    "absences_log": "absences (log1p)",
    "studytime": "weekly study time",
    "higher": "wants higher educ.",
    "goout": "going out",
    "Medu": "mother's education",
}
SCHOOL_LEVELS = ["GP", "MS"]
MJOB_LEVELS = ["at_home", "health", "other", "services", "teacher"]

# Prior hyper-parameters.  "initial" is the first, deliberately vague choice;
# "revised" is the weakly-informative choice adopted after the prior
# predictive check (see p1_prior_predictive.py and the report).
PRIORS = {
    "initial": dict(alpha_loc=0.0, alpha_scale=10.0, beta_scale=5.0, sigma_scale=10.0, group_scale=10.0),
    "revised": dict(alpha_loc=10.0, alpha_scale=3.0, beta_scale=1.0, sigma_scale=5.0, group_scale=2.0),
}


def load_data() -> pd.DataFrame:
    """Load the mathematics data set and add derived columns."""
    df = pd.read_csv(DATA_PATH, sep=";")
    df["absences_log"] = np.log1p(df["absences"])
    df["higher"] = (df["higher"] == "yes").astype(int)
    df["school_idx"] = pd.Categorical(df["school"], categories=SCHOOL_LEVELS).codes
    df["mjob_idx"] = pd.Categorical(df["Mjob"], categories=MJOB_LEVELS).codes
    return df


def design_matrix(df: pd.DataFrame):
    """Standardise the continuous predictors (z-scores); keep ``higher`` as 0/1.

    Returns the matrix ``X`` (n x p), and the means / standard deviations used,
    so that coefficients can be interpreted per one-standard-deviation change.
    """
    X = df[FEATURES].astype(float).copy()
    means = X.mean()
    sds = X.std(ddof=0)
    for f in FEATURES:
        if f == "higher":  # binary: leave as 0/1 so beta is a group difference
            means[f], sds[f] = 0.0, 1.0
            continue
        X[f] = (X[f] - means[f]) / sds[f]
    return jnp.asarray(X.values), means, sds


def get_arrays(df: pd.DataFrame):
    X, means, sds = design_matrix(df)
    school = jnp.asarray(df["school_idx"].values)
    mjob = jnp.asarray(df["mjob_idx"].values)
    y = jnp.asarray(df["G3"].values, dtype=jnp.float32)
    return X, school, mjob, y, means, sds


# --------------------------------------------------------------------------- #
# Models
# --------------------------------------------------------------------------- #
def model_pooled(X, school=None, mjob=None, y=None, prior: str = "revised"):
    """Model 1: complete pooling, individual-level predictors only."""
    hp = PRIORS[prior]
    n, p = X.shape
    alpha = numpyro.sample("alpha", dist.Normal(hp["alpha_loc"], hp["alpha_scale"]))
    beta = numpyro.sample("beta", dist.Normal(0.0, hp["beta_scale"]).expand([p]).to_event(1))
    sigma = numpyro.sample("sigma", dist.HalfNormal(hp["sigma_scale"]))
    mu = numpyro.deterministic("mu", alpha + X @ beta)
    with numpyro.plate("students", n):
        numpyro.sample("G3", dist.Normal(mu, sigma), obs=y)


def model_hier(X, school, mjob, y=None, prior: str = "revised"):
    """Model 2: partial pooling -- varying intercepts by school and by Mjob."""
    hp = PRIORS[prior]
    n, p = X.shape
    n_school, n_mjob = len(SCHOOL_LEVELS), len(MJOB_LEVELS)

    alpha = numpyro.sample("alpha", dist.Normal(hp["alpha_loc"], hp["alpha_scale"]))
    beta = numpyro.sample("beta", dist.Normal(0.0, hp["beta_scale"]).expand([p]).to_event(1))
    sigma = numpyro.sample("sigma", dist.HalfNormal(hp["sigma_scale"]))

    # Group-level scales (how much the groups differ) -- learned from data.
    sigma_school = numpyro.sample("sigma_school", dist.HalfNormal(hp["group_scale"]))
    sigma_mjob = numpyro.sample("sigma_mjob", dist.HalfNormal(hp["group_scale"]))

    # Non-centred varying intercepts: a_g = sigma_g * z_g, z_g ~ Normal(0, 1)
    with numpyro.plate("school", n_school):
        z_school = numpyro.sample("z_school", dist.Normal(0.0, 1.0))
    with numpyro.plate("mjob", n_mjob):
        z_mjob = numpyro.sample("z_mjob", dist.Normal(0.0, 1.0))
    a_school = numpyro.deterministic("a_school", sigma_school * z_school)
    a_mjob = numpyro.deterministic("a_mjob", sigma_mjob * z_mjob)

    mu = numpyro.deterministic("mu", alpha + a_school[school] + a_mjob[mjob] + X @ beta)
    with numpyro.plate("students", n):
        numpyro.sample("G3", dist.Normal(mu, sigma), obs=y)


MODELS = {"M1_pooled": model_pooled, "M2_hier": model_hier}
MODEL_TITLES = {"M1_pooled": "Model 1 (individual, complete pooling)", "M2_hier": "Model 2 (hierarchical, partial pooling)"}
