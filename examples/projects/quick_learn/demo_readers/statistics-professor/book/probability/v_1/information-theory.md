Notation: $\log$ is natural (nats) unless stated; $p,q$ denote pmfs/pdfs w.r.t. a common dominating measure; $\mathbb{E}_p$ is expectation under $X\sim p$.

<!-- note: Rewritten as a terse reference with ML-paper notation; intuition-building prose removed. -->
## Entropy

Discrete: $\mathrm{H}(p) = -\sum_x p(x)\log p(x) = \mathbb{E}_p[-\log p(X)]$. Bounded by $0\le \mathrm{H}\le\log|\mathcal{X}|$, with the upper bound attained iff $p$ is uniform.

Differential: $h(p) = -\int p(x)\log p(x)\,dx$. It is not the limit of discrete entropy under quantization (that differs by a divergent $\log(1/\Delta)$ term), can be negative, and is not invariant under reparametrization: $h(AX+b)=h(X)+\log|\det A|$. Max-entropy facts: Gaussian under fixed covariance, $h=\tfrac12\log\det(2\pi e\Sigma)$; uniform on bounded support.

Chain rule: $\mathrm{H}(X,Y)=\mathrm{H}(X)+\mathrm{H}(Y\mid X)$, with $\mathrm{H}(Y\mid X)=\mathbb{E}_{p(x,y)}[-\log p(y\mid x)]$.

## KL divergence

$$\mathrm{KL}(p\,\|\,q)=\mathbb{E}_p\!\left[\log\frac{p(X)}{q(X)}\right]=\int p\log\frac{p}{q},$$

defined as $+\infty$ unless $p\ll q$. By Jensen applied to $-\log$, $\mathrm{KL}(p\|q)\ge 0$ with equality iff $p=q$ a.e. (Gibbs' inequality). It is not symmetric and does not satisfy the triangle inequality, so it is a divergence, not a metric.

ML convention for the direction:

- Forward $\mathrm{KL}(p_{\text{data}}\|q_\theta)$: mass-covering; this is what MLE minimizes.
- Reverse $\mathrm{KL}(q_\phi\|p)$: mode-seeking; this is the variational inference objective, since $\mathrm{KL}(q_\phi(z)\|p(z\mid x)) = \log p(x) - \mathrm{ELBO}(\phi)$.

## Cross-entropy

$$\mathrm{H}(p,q)=-\mathbb{E}_p[\log q(X)]=\mathrm{H}(p)+\mathrm{KL}(p\|q).$$

With the empirical distribution $\hat p_n$, $\mathrm{H}(\hat p_n,q_\theta)=-\frac1n\sum_i\log q_\theta(x_i)$, i.e. the average negative log-likelihood. Minimizing cross-entropy over $\theta$, minimizing forward KL to $\hat p_n$, and MLE are therefore equivalent. In classification, $q_\theta(y\mid x)=\mathrm{softmax}(f_\theta(x))_y$ and the loss is $-\log q_\theta(y\mid x)$.

## Mutual information

$$I(X;Y)=\mathrm{KL}\big(p_{X,Y}\,\|\,p_X\otimes p_Y\big)=\mathrm{H}(X)-\mathrm{H}(X\mid Y)=\mathrm{H}(X)+\mathrm{H}(Y)-\mathrm{H}(X,Y).$$

It is symmetric and non-negative, and $I(X;Y)=0$ iff $X\perp Y$. It is invariant under invertible reparametrizations of $X$ and $Y$ individually. Conditional version: $I(X;Y\mid Z)=\mathbb{E}_{p(z)}\big[\mathrm{KL}(p_{X,Y|Z}\|p_{X|Z}\,p_{Y|Z})\big]$. Chain rule: $I(X;Y,Z)=I(X;Z)+I(X;Y\mid Z)$. Data processing: if $X\to Y\to Z$ is Markov, then $I(X;Z)\le I(X;Y)$. This underlies the information bottleneck and the InfoNCE-type lower bounds used in contrastive learning.

## Fisher information

For a model $p(x;\theta)$ with score $s_\theta(x)=\nabla_\theta\log p(x;\theta)$, under regularity conditions $\mathbb{E}[s_\theta]=0$ and

$$\mathcal{F}(\theta)=\mathbb{E}_{x\sim p_\theta}\!\left[s_\theta(x)s_\theta(x)^\top\right]=-\mathbb{E}_{p_\theta}\!\left[\nabla^2_\theta\log p(x;\theta)\right]\in\mathbb{S}^d_{+}.$$

Note that the expectation is under the model, not the data. In ML this distinction separates the true Fisher from the *empirical Fisher*, which uses data labels and is generally not equal to it.

Links to KL: $\mathrm{KL}(p_\theta\|p_{\theta+\delta})=\tfrac12\delta^\top\mathcal{F}(\theta)\delta+O(\|\delta\|^3)$, so $\mathcal{F}$ is the Riemannian metric of the statistical manifold. Natural gradient: $\theta\leftarrow\theta-\eta\,\mathcal{F}(\theta)^{-1}\nabla_\theta\mathcal{L}$.

Cramér–Rao: for unbiased $\hat\theta$ from $n$ i.i.d. samples, $\mathrm{Cov}(\hat\theta)\succeq \frac1n\mathcal{F}(\theta)^{-1}$. The MLE attains this asymptotically: $\sqrt n(\hat\theta_{\text{MLE}}-\theta)\xrightarrow{d}\mathcal{N}(0,\mathcal{F}(\theta)^{-1})$.
