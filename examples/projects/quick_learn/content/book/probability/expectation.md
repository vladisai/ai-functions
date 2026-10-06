---
topics:
  - "expectation, linearity of expectation"
  - "variance, covariance"
  - tower property (law of iterated expectations)
  - total variance (law of total variance)
---

# Expectation and Moments

The **expectation** $\mathbb{E}[X]$ is the probability-weighted average of a random variable — $\sum_x x\,p(x)$ for discrete RVs, $\int x\,f(x)\,dx$ for continuous ones. It answers "if I sampled $X$ over and over, what would I get on average?" Its most useful property is **linearity**: $\mathbb{E}[aX + bY] = a\mathbb{E}[X] + b\mathbb{E}[Y]$, and this holds *regardless* of whether $X$ and $Y$ are dependent. That unconditional linearity is surprisingly powerful — it's the reason you can compute expected losses by summing over individual terms without worrying about correlations.

## Variance and Covariance

**Variance** $\text{Var}[X] = \mathbb{E}[(X - \mathbb{E}[X])^2] = \mathbb{E}[X^2] - (\mathbb{E}[X])^2$ quantifies the spread of a distribution. Unlike expectation, variance is *not* linear: $\text{Var}[aX] = a^2\text{Var}[X]$, and for independent $X,Y$ you get $\text{Var}[X+Y] = \text{Var}[X] + \text{Var}[Y]$ — but that sum breaks down when they're dependent.

**Covariance** $\text{Cov}[X,Y] = \mathbb{E}[XY] - \mathbb{E}[X]\mathbb{E}[Y]$ captures how two variables move together. Positive covariance means they tend to increase in tandem; negative means one goes up when the other goes down; zero means they're linearly unrelated (but possibly dependent in other ways). Normalizing covariance by the standard deviations gives **correlation** $\rho_{X,Y} = \text{Cov}[X,Y]/(\sigma_X \sigma_Y) \in [-1, 1]$.

For a random vector $\mathbf{X} = (X_1, \ldots, X_n)$, the **covariance matrix** $\Sigma_{ij} = \text{Cov}[X_i, X_j]$ packages all pairwise relationships into one positive semi-definite matrix. This matrix shows up everywhere — it parameterizes multivariate Gaussians, defines Mahalanobis distance, and its eigenstructure is what PCA decomposes.

## Conditional Expectations

Two results connect marginal and conditional moments, and both come up constantly in derivations.

The **tower property** (law of iterated expectations) says $\mathbb{E}[X] = \mathbb{E}[\mathbb{E}[X \mid Y]]$ — you can compute an expectation by first conditioning on $Y$, then averaging over $Y$. This is the workhorse behind things like the reparameterization trick and EM algorithms.

The **law of total variance** $\text{Var}[X] = \mathbb{E}[\text{Var}[X|Y]] + \text{Var}[\mathbb{E}[X|Y]]$ decomposes total variance into within-group variation (first term) and between-group variation (second term). In an ANOVA context, this is literally the partitioning of sum of squares.

## Inequalities and Generating Functions

Three inequalities appear repeatedly in proofs and give useful back-of-the-envelope bounds:

- **Markov's**: $P(X \geq a) \leq \mathbb{E}[X]/a$ for non-negative $X$. Crude but universal.
- **Chebyshev's**: $P(|X - \mu| \geq k\sigma) \leq 1/k^2$. Tighter — uses variance — but still distribution-free.
- **Jensen's**: $\mathbb{E}[g(X)] \geq g(\mathbb{E}[X])$ for convex $g$ (flip for concave). This one is everywhere — it's the reason the ELBO is a lower bound, why log-likelihood objectives work the way they do, and why you can't just swap $\log$ and $\mathbb{E}$ without paying a price.

The **moment generating function** $M_X(t) = \mathbb{E}[e^{tX}]$ is a compact encoding of all moments: the $n$-th derivative at $t=0$ gives $\mathbb{E}[X^n]$. When it exists, the MGF uniquely determines the distribution. For independent variables, MGFs multiply: $M_{X+Y}(t) = M_X(t) \cdot M_Y(t)$, which makes it easy to find distributions of sums.
