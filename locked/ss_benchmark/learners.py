"""Nuisance learners (§9) and probe learners (§5); implementation notes N1-N5, N9.

* Ridge: z-scored features (fit-row mean / SD; SD 0 -> 1), intercept unpenalised, objective SSE + λ||b||²; λ by inner
  5-fold CV (MSE) over {1e-3..1e3}; ties -> larger λ.
* L2 logistic (binary): objective Σ log-loss + (λ/2)||b||² on z-scored features, damped Newton; λ by inner 5-fold CV
  (mean log-loss); ties -> larger λ. Multinomial (site probe): same objective with L-BFGS.
* MLP: Linear(p, h) -> ReLU -> Linear(h, out); PyTorch nn.Linear default init (U(±1/sqrt(fan_in))); Adam (0.9, 0.999,
  1e-8), lr 1e-3, weight decay 1e-4 added to every parameter's gradient; mini-batch min(200, n_fit) reshuffled each
  epoch; z-scored inputs (and outputs for regression); early stopping on a 20 % inner validation split (by group),
  patience in epochs without strict improvement of the validation loss; best-epoch parameters restored.
* Learner choice (N4): each learner procedure is scored by 5-fold group CV inside the training data; lower loss wins
  (ties -> linear learner); the winner is refitted on all training rows.
All randomness comes from the numpy Generator passed in.
"""
import numpy as np
from scipy.optimize import minimize
from scipy.special import expit, log_expit, logsumexp

from .constants import INNER_FOLDS, MLP_NUISANCE, PENALTY_GRID_NUISANCE


# ---------------------------------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------------------------------
def zscore_params(X):
    mu = X.mean(0)
    sd = X.std(0)
    sd = np.where(sd > 0, sd, 1.0)
    return mu, sd


def group_kfold(groups, n_splits, rng):
    """Return a list of (train_rows, test_rows) splitting unique groups into n_splits folds at random."""
    ug = np.unique(groups)
    perm = ug[rng.permutation(len(ug))]
    gfold = np.empty(len(ug), dtype=np.int64)
    gfold[np.searchsorted(ug, perm)] = np.arange(len(ug)) % n_splits
    row_fold = gfold[np.searchsorted(ug, groups)]
    return [(np.flatnonzero(row_fold != k), np.flatnonzero(row_fold == k)) for k in range(n_splits)]


def group_holdout(groups, fraction, rng):
    ug = np.unique(groups)
    n_val = int(round(fraction * len(ug)))
    n_val = min(max(n_val, 1), len(ug) - 1)
    val_groups = ug[rng.permutation(len(ug))[:n_val]]
    is_val = np.isin(groups, val_groups)
    return np.flatnonzero(~is_val), np.flatnonzero(is_val)


def mean_logloss_from_logit(eta, y):
    return float(np.mean(-(y * log_expit(eta) + (1 - y) * log_expit(-eta))))


# ---------------------------------------------------------------------------------------------------------------------
# ridge
# ---------------------------------------------------------------------------------------------------------------------
def _ridge_path(Xtr, ytr, Xte, grid):
    mu, sd = zscore_params(Xtr)
    Z = (Xtr - mu) / sd
    ym = ytr.mean()
    U, s, Vt = np.linalg.svd(Z, full_matrices=False)
    Uy = U.T @ (ytr - ym)
    lam = np.asarray(grid, float)
    D = (s / (s ** 2 + lam[:, None])) * Uy           # (G, r)
    coefs = D @ Vt                                     # (G, p) in z-units
    return ym + ((Xte - mu) / sd) @ coefs.T, (mu, sd, ym, coefs)


class RidgeModel:
    def __init__(self, mu, sd, intercept, coef, lam):
        self.mu, self.sd, self.intercept, self.coef, self.lam = mu, sd, intercept, coef, lam
        self.name = "ridge"

    def predict(self, X):
        return self.intercept + ((X - self.mu) / self.sd) @ self.coef


def fit_ridge_cv(X, y, groups, rng, grid=PENALTY_GRID_NUISANCE, n_inner=INNER_FOLDS):
    sse = np.zeros(len(grid))
    for tr, te in group_kfold(groups, n_inner, rng):
        pred, _ = _ridge_path(X[tr], y[tr], X[te], grid)
        sse += ((pred - y[te, None]) ** 2).sum(0)
    best = _argmin_prefer_last(sse)
    _, (mu, sd, ym, coefs) = _ridge_path(X, y, X[:1], grid)
    return RidgeModel(mu, sd, ym, coefs[best], grid[best])


def _argmin_prefer_last(v):
    v = np.asarray(v)
    return int(len(v) - 1 - np.argmin(v[::-1]))


# ---------------------------------------------------------------------------------------------------------------------
# L2 logistic regression
# ---------------------------------------------------------------------------------------------------------------------
def _logistic_newton(Z, y, lam, b0=None, max_iter=100):
    n, p = Z.shape
    Z1 = np.hstack([np.ones((n, 1)), Z])
    pen = np.full(p + 1, lam); pen[0] = 0.0
    b = np.zeros(p + 1) if b0 is None else b0.copy()

    def obj(b):
        eta = Z1 @ b
        return float(np.sum(np.logaddexp(0.0, eta) - y * eta) + 0.5 * np.sum(pen * b * b))

    f = obj(b)
    for _ in range(max_iter):
        eta = Z1 @ b
        mu = expit(eta)
        g = Z1.T @ (mu - y) + pen * b
        w = mu * (1 - mu)
        H = (Z1 * w[:, None]).T @ Z1 + np.diag(pen) + 1e-12 * np.eye(p + 1)
        step = np.linalg.solve(H, g)
        t = 1.0
        while True:
            b_new = b - t * step
            f_new = obj(b_new)
            if f_new <= f + 1e-12 * abs(f) or t < 1e-10:
                break
            t *= 0.5
        converged = np.max(np.abs(b_new - b)) < 1e-10 * (1 + np.max(np.abs(b))) or abs(f - f_new) < 1e-13 * (1 + abs(f))
        b, f = b_new, f_new
        if converged:
            break
    return b


class LogisticModel:
    def __init__(self, mu, sd, b, lam):
        self.mu, self.sd, self.b, self.lam = mu, sd, b, lam
        self.name = "logistic"

    def logit(self, X):
        return self.b[0] + ((X - self.mu) / self.sd) @ self.b[1:]


def _logistic_path(Xtr, ytr, grid):
    mu, sd = zscore_params(Xtr)
    Z = (Xtr - mu) / sd
    order = np.argsort(grid)[::-1]                    # strong -> weak penalty, warm starts
    bs = [None] * len(grid)
    b = None
    for k in order:
        b = _logistic_newton(Z, ytr, grid[k], b)
        bs[k] = b
    return mu, sd, bs


def fit_logistic_cv(X, y, groups, rng, grid=PENALTY_GRID_NUISANCE, n_inner=INNER_FOLDS):
    loss = np.zeros(len(grid))
    for tr, te in group_kfold(groups, n_inner, rng):
        mu, sd, bs = _logistic_path(X[tr], y[tr], grid)
        Zte = (X[te] - mu) / sd
        for k, b in enumerate(bs):
            eta = b[0] + Zte @ b[1:]
            loss[k] += np.sum(-(y[te] * log_expit(eta) + (1 - y[te]) * log_expit(-eta)))
    best = _argmin_prefer_last(loss)
    mu, sd, bs = _logistic_path(X, y, [grid[best]])
    return LogisticModel(mu, sd, bs[0], grid[best])


# multinomial (site probe)
class MultinomialModel:
    def __init__(self, mu, sd, B, lam, classes):
        self.mu, self.sd, self.B, self.lam, self.classes = mu, sd, B, lam, classes
        self.name = "multinomial"

    def logits(self, X):
        Z = (X - self.mu) / self.sd
        return self.B[0] + Z @ self.B[1:]

    def predict_proba(self, X):
        L = self.logits(X)
        return np.exp(L - logsumexp(L, axis=1, keepdims=True))


def _multinomial_fit(Z, yk, n_classes, lam, B0=None):
    n, p = Z.shape
    Y = np.zeros((n, n_classes)); Y[np.arange(n), yk] = 1.0
    Z1 = np.hstack([np.ones((n, 1)), Z])
    pen = np.full((p + 1, 1), lam); pen[0] = 0.0

    def fg(theta):
        B = theta.reshape(p + 1, n_classes)
        L = Z1 @ B
        lse = logsumexp(L, axis=1, keepdims=True)
        f = float(np.sum(lse) - np.sum(Y * L) + 0.5 * np.sum(pen * B * B))
        P = np.exp(L - lse)
        G = Z1.T @ (P - Y) + pen * B
        return f, G.ravel()

    x0 = np.zeros((p + 1) * n_classes) if B0 is None else B0.ravel()
    res = minimize(fg, x0, jac=True, method="L-BFGS-B", options=dict(maxiter=5000, gtol=1e-8, ftol=1e-14, maxcor=20))
    return res.x.reshape(p + 1, n_classes)


def fit_multinomial_cv(X, y, groups, rng, grid, n_inner=INNER_FOLDS):
    classes, yk = np.unique(y, return_inverse=True)
    C = len(classes)
    loss = np.zeros(len(grid))
    order = np.argsort(grid)[::-1]
    for tr, te in group_kfold(groups, n_inner, rng):
        mu, sd = zscore_params(X[tr])
        Ztr, Zte = (X[tr] - mu) / sd, (X[te] - mu) / sd
        B = None
        for k in order:
            B = _multinomial_fit(Ztr, yk[tr], C, grid[k], B)
            L = B[0] + Zte @ B[1:]
            loss[k] += np.sum(logsumexp(L, axis=1) - L[np.arange(len(te)), yk[te]])
    best = _argmin_prefer_last(loss)
    mu, sd = zscore_params(X)
    B = _multinomial_fit((X - mu) / sd, yk, C, grid[best])
    return MultinomialModel(mu, sd, B, grid[best], classes)


# ---------------------------------------------------------------------------------------------------------------------
# MLP (numpy)
# ---------------------------------------------------------------------------------------------------------------------
class MLP:
    """task: 'reg' (MSE), 'bin' (logit output, BCE), 'multi' (softmax, CE)."""

    def __init__(self, task, hidden, lr, weight_decay, max_epochs, patience, val_fraction):
        self.task, self.hidden, self.lr, self.wd = task, hidden, lr, weight_decay
        self.max_epochs, self.patience, self.val_fraction = max_epochs, patience, val_fraction
        self.name = "mlp"

    # -- core -----------------------------------------------------------------------------------------------------
    def _forward(self, Z, params):
        W1, b1, W2, b2 = params
        Hpre = Z @ W1 + b1
        H = np.maximum(Hpre, 0.0)
        return Hpre, H, H @ W2 + b2

    def _loss_grad_out(self, out, y):
        n = out.shape[0]
        if self.task == "reg":
            r = out - y
            return float(np.mean(r * r)), 2.0 * r / n
        if self.task == "bin":
            eta = out[:, 0]
            loss = float(np.mean(np.logaddexp(0.0, eta) - y * eta))
            return loss, ((expit(eta) - y) / n)[:, None]
        lse = logsumexp(out, axis=1, keepdims=True)
        loss = float(np.mean(lse[:, 0] - out[np.arange(n), y]))
        P = np.exp(out - lse)
        P[np.arange(n), y] -= 1.0
        return loss, P / n

    def _loss(self, out, y):
        if self.task == "reg":
            r = out - y
            return float(np.mean(r * r))
        if self.task == "bin":
            eta = out[:, 0]
            return float(np.mean(np.logaddexp(0.0, eta) - y * eta))
        lse = logsumexp(out, axis=1)
        return float(np.mean(lse - out[np.arange(out.shape[0]), y]))

    def fit(self, X, y, rng, groups=None, n_classes=None):
        n, p = X.shape
        groups = np.arange(n) if groups is None else groups
        fit_rows, val_rows = group_holdout(groups, self.val_fraction, rng)
        self.mu, self.sd = zscore_params(X[fit_rows])
        Z = (X - self.mu) / self.sd
        if self.task == "reg":
            self.ymu, self.ysd = float(y[fit_rows].mean()), float(y[fit_rows].std()) or 1.0
            T = ((y - self.ymu) / self.ysd)[:, None]
            n_out = 1
        elif self.task == "bin":
            T = y.astype(np.float64)
            n_out = 1
        else:
            T = y.astype(np.int64)
            n_out = n_classes
        h = self.hidden
        b1_ = 1.0 / np.sqrt(p) if p > 0 else 1.0
        b2_ = 1.0 / np.sqrt(h)
        init = [rng.uniform(-b1_, b1_, (p, h)), rng.uniform(-b1_, b1_, h),
                rng.uniform(-b2_, b2_, (h, n_out)), rng.uniform(-b2_, b2_, n_out)]
        shapes = [q.shape for q in init]
        theta = np.concatenate([q.ravel() for q in init])      # flat parameter vector; views below
        grad = np.zeros_like(theta)
        params = self._views(theta, shapes)
        grads = self._views(grad, shapes)
        m = np.zeros_like(theta)
        v = np.zeros_like(theta)
        beta1, beta2, eps = 0.9, 0.999, 1e-8
        Zf, Tf = Z[fit_rows], T[fit_rows]
        Zv, Tv = Z[val_rows], T[val_rows]
        nf = len(fit_rows)
        bs = min(200, nf)
        best = np.inf
        best_theta = theta.copy()
        since = 0
        step = 0
        self.epochs_run = 0
        for epoch in range(self.max_epochs):
            order = rng.permutation(nf)
            for start in range(0, nf, bs):
                idx = order[start:start + bs]
                Zb, Tb = Zf[idx], Tf[idx]
                Hpre, H, out = self._forward(Zb, params)
                _, dout = self._loss_grad_out(out, Tb)
                np.dot(H.T, dout, out=grads[2])
                np.sum(dout, axis=0, out=grads[3])
                dH = dout @ params[2].T
                dH[Hpre <= 0] = 0.0
                np.dot(Zb.T, dH, out=grads[0])
                np.sum(dH, axis=0, out=grads[1])
                step += 1
                c1 = 1 - beta1 ** step
                c2 = 1 - beta2 ** step
                grad += self.wd * theta
                m *= beta1; m += (1 - beta1) * grad
                v *= beta2; v += (1 - beta2) * grad * grad
                theta -= self.lr * (m / c1) / (np.sqrt(v / c2) + eps)
            self.epochs_run = epoch + 1
            vl = self._loss(self._forward(Zv, params)[2], Tv)
            if vl < best:
                best = vl
                best_theta[:] = theta
                since = 0
            else:
                since += 1
                if since >= self.patience:
                    break
        self.params = self._views(best_theta, shapes)
        self.best_val_loss = best
        return self

    @staticmethod
    def _views(flat, shapes):
        out, pos = [], 0
        for s in shapes:
            size = int(np.prod(s))
            out.append(flat[pos:pos + size].reshape(s))
            pos += size
        return out

    def _out(self, X):
        return self._forward((X - self.mu) / self.sd, self.params)[2]

    def predict(self, X):
        return self._out(X)[:, 0] * self.ysd + self.ymu

    def logit(self, X):
        return self._out(X)[:, 0]

    def predict_proba(self, X):
        L = self._out(X)
        return np.exp(L - logsumexp(L, axis=1, keepdims=True))


def nuisance_mlp(task):
    return MLP(task, **MLP_NUISANCE)


# ---------------------------------------------------------------------------------------------------------------------
# learner choice by CV loss within the training data (N4)
# ---------------------------------------------------------------------------------------------------------------------
def fit_outcome(X, y, groups, rng, mode="select"):
    """Outcome regression: ridge, or ridge vs MLP by 5-fold group-CV MSE (mode 'select')."""
    if mode == "linear":
        return fit_ridge_cv(X, y, groups, rng), dict(learner="ridge", cv=None)
    sse = np.zeros(2)
    for tr, te in group_kfold(groups, INNER_FOLDS, rng):
        r = fit_ridge_cv(X[tr], y[tr], groups[tr], rng)
        nn = nuisance_mlp("reg").fit(X[tr], y[tr], rng, groups[tr])
        sse[0] += np.sum((r.predict(X[te]) - y[te]) ** 2)
        sse[1] += np.sum((nn.predict(X[te]) - y[te]) ** 2)
    cv = (sse / len(y)).tolist()
    if sse[1] < sse[0]:
        return nuisance_mlp("reg").fit(X, y, rng, groups), dict(learner="mlp", cv=cv)
    return fit_ridge_cv(X, y, groups, rng), dict(learner="ridge", cv=cv)


def fit_classifier(X, y, groups, rng, mode="select"):
    """Binary classifier with a .logit(): L2 logistic, or logistic vs MLP by 5-fold group-CV log-loss."""
    if mode == "linear":
        return fit_logistic_cv(X, y, groups, rng), dict(learner="logistic", cv=None)
    loss = np.zeros(2)
    for tr, te in group_kfold(groups, INNER_FOLDS, rng):
        lg = fit_logistic_cv(X[tr], y[tr], groups[tr], rng)
        nn = nuisance_mlp("bin").fit(X[tr], y[tr], rng, groups[tr])
        loss[0] += len(te) * mean_logloss_from_logit(lg.logit(X[te]), y[te])
        loss[1] += len(te) * mean_logloss_from_logit(nn.logit(X[te]), y[te])
    cv = (loss / len(y)).tolist()
    if loss[1] < loss[0]:
        return nuisance_mlp("bin").fit(X, y, rng, groups), dict(learner="mlp", cv=cv)
    return fit_logistic_cv(X, y, groups, rng), dict(learner="logistic", cv=cv)
