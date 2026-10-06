<!-- note: Tightened to a reference style in ML notation; added integrability caveats and the vector forms. -->
Notation: $\mathbb{E}_{x\sim p}[f(x)] = \sum_x p(x) f(x)$ or $\int f(x)\,p(x)\,dx$, with the subscript naming the sampling distribution (essential in ML papers, where it often carries the dependence on parameters, e.g. $\mathbb{E}_{z\sim q_\phi}[\cdot]$). Throughout, assume the relevant moments exist.

## Expectation

$\mathbb{E}[X] = \int x\,p(x)\,dx$ (a sum in the discrete case). For measurable $g$, the law of the unconscious statistician gives $\mathbb{E}[g(X)] = \int g(x)\,p(x)\,dx$, with no need to derive the law of $g(X)$.

**Linearity** holds with no independence assumption, only integrability:
$$\mathbb{E}[aX + bY] = a\,\mathbb{E}[X] + b\,\mathbb{E}[Y].$$
For vectors and matrices, $\mathbb{E}[A\mathbf{X} + \mathbf{b}] = A\,\mathbb{E}[\mathbf{X}] + \mathbf{b}$. Expectation is not multiplicative in general: $\mathbb{E}[XY] = \mathbb{E}[X]\,\mathbb{E}[Y]$ if $X \perp Y$, but the converse fails.

## Variance and Covariance

$$\text{Var}[X] = \mathbb{E}[(X-\mathbb{E}X)^2] = \mathbb{E}[X^2] - \mathbb{E}[X]^2,\qquad \text{Var}[aX+b] = a^2\,\text{Var}[X].$$

$$\text{Cov}[X,Y] = \mathbb{E}[(X-\mathbb{E}X)(Y-\mathbb{E}Y)] = \mathbb{E}[XY]-\mathbb{E}[X]\,\mathbb{E}[Y].$$

In general,
$$\text{Var}[X+Y] = \text{Var}[X] + \text{Var}[Y] + 2\,\text{Cov}[X,Y],$$
and the cross term vanishes when $X,Y$ are uncorrelated (in particular when independent). Zero covariance does not imply independence. For $n$ variables, $\text{Var}[\sum_i X_i] = \sum_{i,j}\text{Cov}[X_i,X_j]$.

Correlation: $\rho_{XY} = \text{Cov}[X,Y]/(\sigma_X\sigma_Y)\in[-1,1]$ by Cauchy–Schwarz.

For $\mathbf{X}\in\mathbb{R}^n$, the covariance matrix is
$$\Sigma = \text{Cov}[\mathbf{X}] = \mathbb{E}[(\mathbf{X}-\boldsymbol\mu)(\mathbf{X}-\boldsymbol\mu)^\top] = \mathbb{E}[\mathbf{X}\mathbf{X}^\top]-\boldsymbol\mu\boldsymbol\mu^\top \succeq 0,$$
with $\text{Cov}[A\mathbf{X}+\mathbf{b}] = A\Sigma A^\top$. It parameterizes $\mathcal{N}(\boldsymbol\mu,\Sigma)$, defines Mahalanobis distance, and its eigendecomposition is PCA.

## Conditional Expectations

**Tower property** (law of iterated expectations):
$$\mathbb{E}[X] = \mathbb{E}_Y\big[\mathbb{E}[X\mid Y]\big].$$
More generally, $\mathbb{E}[X\mid\mathcal{G}] = \mathbb{E}[\mathbb{E}[X\mid\mathcal{H}]\mid\mathcal{G}]$ for $\mathcal{G}\subseteq\mathcal{H}$. It underlies the derivations of EM, policy-gradient baselines, and Rao–Blackwellization, where conditioning never increases variance.

**Law of total variance:**
$$\text{Var}[X] = \mathbb{E}_Y\big[\text{Var}[X\mid Y]\big] + \text{Var}_Y\big(\mathbb{E}[X\mid Y]\big).$$
This is the unexplained plus explained variance decomposition, i.e. the $L^2$ Pythagorean identity for the projection $\mathbb{E}[X\mid Y]$. The multivariate version replaces $\text{Var}$ with $\text{Cov}$.

## Inequalities and Generating Functions

- **Markov:** $P(X\ge a)\le \mathbb{E}[X]/a$ for $X\ge0$, $a>0$.
- **Chebyshev:** $P(|X-\mu|\ge k\sigma)\le 1/k^2$.
- **Jensen:** for convex $g$, $g(\mathbb{E}[X])\le\mathbb{E}[g(X)]$, with equality for strictly convex $g$ iff $X$ is a.s. constant. Applied to $\log$ (concave), it gives $\log\mathbb{E}_q[w]\ge\mathbb{E}_q[\log w]$, which is the ELBO bound: $\log p(x) = \log \mathbb{E}_{q}\!\big[\tfrac{p(x,z)}{q(z)}\big]\ge \mathbb{E}_q\!\big[\log\tfrac{p(x,z)}{q(z)}\big]$.

**Moment generating function:** $M_X(t)=\mathbb{E}[e^{tX}]$. If it is finite on a neighborhood of $0$, then $M_X^{(n)}(0)=\mathbb{E}[X^n]$ and $M_X$ determines the law. For independent $X,Y$, $M_{X+Y}=M_X M_Y$. Where the MGF may not exist (e.g. heavy tails), use the characteristic function $\varphi_X(t)=\mathbb{E}[e^{itX}]$, which always does.
