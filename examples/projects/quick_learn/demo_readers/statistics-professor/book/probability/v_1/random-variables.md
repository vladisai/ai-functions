A random variable is a measurable map $X:\Omega\to\mathbb{R}^d$. Its law is the pushforward $P_X = P\circ X^{-1}$. ML papers usually suppress $(\Omega,\mathcal F,P)$ and write $x\sim p(x)$, using $p$ for both PMFs and densities with respect to counting or Lebesgue measure (more generally, a base measure $\mu$). Variables are distinguished by their arguments, so $p(x)$ and $p(y)$ are different functions. Capital letters are often dropped, and $\mathbb{E}_{x\sim p}[f(x)]$ replaces $\int f\,dP_X$.

<!-- note: Condensed to reference style; dropped primer-level explanations you don't need -->
## Probability Functions

- Discrete: PMF $p(x)=P(X=x)$, $\sum_x p(x)=1$.
- Continuous (absolutely continuous law): density $p(x)=\frac{dP_X}{d\lambda}(x)$, with $P(X\in A)=\int_A p(x)\,dx$. Densities can exceed 1; only integrals are bounded.
- CDF: $F(x)=P(X\le x)$. If $F$ is differentiable, $p=F'$ a.e.

Mixed and singular laws exist, but ML papers almost always assume one of the two cases above. Singular laws matter when data lie on a low-dimensional manifold, where the density with respect to Lebesgue measure does not exist. This is a known failure mode for GANs and for likelihood-based models with ambient-dimension densities.

<!-- note: Switched to ML notation: p(x,y), p(y|x), with no subscripts on p -->
## Joint, Marginal, and Conditional Distributions

The joint is $p(x,y)$. Marginalization:

$$p(x)=\sum_y p(x,y)\qquad\text{or}\qquad p(x)=\int p(x,y)\,dy.$$

The conditional is $p(y\mid x)=p(x,y)/p(x)$ for $p(x)>0$. In the continuous case it is defined only up to $p(x)\,dx$-null sets, since it is a regular conditional distribution (disintegration). The chain rule is

$$p(x_{1:n})=\prod_{i=1}^n p(x_i\mid x_{<i}),$$

which underlies autoregressive models. Bayes' rule:

$$p(\theta\mid x)=\frac{p(x\mid\theta)\,p(\theta)}{\int p(x\mid\theta')\,p(\theta')\,d\theta'}.$$

The denominator is the evidence (marginal likelihood) $p(x)$, which is typically intractable and motivates variational inference and MCMC.

<!-- note: Added parameterizations and ML usage; removed Poisson from the list's emphasis but kept it terse -->
## Key Distributions

- **Bernoulli** $\mathrm{Bern}(p)$: $p(x)=p^x(1-p)^{1-x}$, $x\in\{0,1\}$. Mean $p$, variance $p(1-p)$. Often parameterized by a logit $\ell$ with $p=\sigma(\ell)$.
- **Categorical** $\mathrm{Cat}(\boldsymbol\pi)$: $p(x=k)=\pi_k$ on the simplex $\Delta^{K-1}$. Usually $\boldsymbol\pi=\mathrm{softmax}(\mathbf z)$, so $\pi_k=e^{z_k}/\sum_j e^{z_j}$. $x$ is often written one-hot, giving $p(x)=\prod_k\pi_k^{x_k}$.
- **Poisson** $\mathrm{Poisson}(\lambda)$: $p(k)=\lambda^k e^{-\lambda}/k!$. Mean and variance both equal $\lambda$.
- **Uniform** $\mathcal U(a,b)$: $p(x)=\frac{1}{b-a}\mathbf 1_{[a,b]}(x)$. Mean $\frac{a+b}{2}$, variance $\frac{(b-a)^2}{12}$.
- **Gaussian** $\mathcal N(\mu,\sigma^2)$: $p(x)=(2\pi\sigma^2)^{-1/2}\exp\!\big(-\frac{(x-\mu)^2}{2\sigma^2}\big)$. It is the maximum-entropy law for given mean and variance. The notation $\mathcal N(x;\mu,\sigma^2)$ is used when the argument must be explicit.
- **Multivariate Gaussian** $\mathcal N(\boldsymbol\mu,\boldsymbol\Sigma)$, $\boldsymbol\Sigma\succ0$:
$$p(\mathbf x)=(2\pi)^{-d/2}|\boldsymbol\Sigma|^{-1/2}\exp\!\big(-\tfrac12(\mathbf x-\boldsymbol\mu)^\top\boldsymbol\Sigma^{-1}(\mathbf x-\boldsymbol\mu)\big).$$
  Closed under affine maps, marginalization, and conditioning. For the block partition $(\mathbf x_a,\mathbf x_b)$:
$$\mathbf x_a\mid\mathbf x_b\sim\mathcal N\big(\boldsymbol\mu_a+\boldsymbol\Sigma_{ab}\boldsymbol\Sigma_{bb}^{-1}(\mathbf x_b-\boldsymbol\mu_b),\ \boldsymbol\Sigma_{aa}-\boldsymbol\Sigma_{ab}\boldsymbol\Sigma_{bb}^{-1}\boldsymbol\Sigma_{ba}\big).$$
  Sampling uses $\mathbf x=\boldsymbol\mu+\mathbf L\boldsymbol\epsilon$ with $\boldsymbol\Sigma=\mathbf L\mathbf L^\top$ and $\boldsymbol\epsilon\sim\mathcal N(\mathbf 0,\mathbf I)$. This is the reparameterization used in VAEs. Diagonal $\boldsymbol\Sigma$ is the common default for latent posteriors. Gaussian processes are the infinite-dimensional analogue.
