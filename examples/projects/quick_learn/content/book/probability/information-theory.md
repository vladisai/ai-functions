---
topics:
  - entropy (discrete and differential)
  - "KL divergence, asymmetry, non-negativity"
  - "cross-entropy, relation to KL"
  - mutual information
  - Fisher information
---

# Information-Theoretic Quantities

Information theory gives us a precise language for uncertainty, surprise, and the gap between distributions. These concepts thread through almost every loss function and inference method in modern ML, so it's worth building a solid intuition for each one.

**Shannon entropy** $\mathrm{H}(X) = -\sum_x p(x)\log p(x)$ measures the average surprise of a discrete random variable — how many bits (if using $\log_2$) or nats (if using $\ln$) you need to encode a sample. High entropy means the distribution is spread out and hard to predict; low entropy means it's concentrated and predictable. The uniform distribution maximizes entropy for a given support. The continuous version, **differential entropy**, replaces the sum with an integral and can go negative (a common gotcha — it measures something subtly different from discrete entropy).

**KL divergence** $\mathrm{KL}(p \| q) = \mathbb{E}_p[\log \frac{p(x)}{q(x)}]$ measures how much information you lose when you use distribution $q$ to approximate the true distribution $p$. It's always non-negative (by Gibbs' inequality) and equals zero only when $p = q$. The critical thing to remember: KL divergence is **not symmetric**. $\mathrm{KL}(p\|q)$ and $\mathrm{KL}(q\|p)$ can be wildly different, which is why the choice of direction matters so much in variational inference. The forward KL ($\mathrm{KL}(p\|q)$) penalizes $q$ for putting low mass where $p$ has high mass (mode-covering); the reverse KL ($\mathrm{KL}(q\|p)$) penalizes $q$ for putting high mass where $p$ has low mass (mode-seeking).

**Cross-entropy** $\mathrm{H}(p, q) = -\mathbb{E}_p[\log q(X)] = \mathrm{H}(p) + \mathrm{KL}(p\|q)$ is the expected log-loss when the true distribution is $p$ but your model predicts $q$. Since $\mathrm{H}(p)$ is constant with respect to $q$, minimizing cross-entropy is the same as minimizing KL divergence — which is exactly why cross-entropy is the standard classification loss. When someone says "minimize negative log-likelihood," they're saying the same thing.

**Mutual information** $I(X;Y) = \mathrm{KL}(p(x,y) \| p(x)p(y)) = \mathrm{H}(X) - \mathrm{H}(X|Y)$ measures how much knowing $Y$ tells you about $X$. Unlike correlation, mutual information captures *any* kind of statistical dependence, not just linear relationships. It's symmetric ($I(X;Y) = I(Y;X)$) and non-negative, with zero meaning $X$ and $Y$ are independent. The **chain rule for entropy** $\mathrm{H}(X,Y) = \mathrm{H}(X) + \mathrm{H}(Y|X)$ and **conditional mutual information** $I(X;Y|Z) = \mathrm{H}(X|Z) - \mathrm{H}(X|Y,Z)$ let you decompose information across multiple variables — these show up in information bottleneck methods and feature selection.

**Fisher information** bridges information theory and estimation. The scalar version $\mathcal{F}(\theta) = \mathbb{E}[(\frac{\partial}{\partial\theta}\log p(X;\theta))^2]$ measures how sensitive a likelihood function is to changes in its parameter — high Fisher information means the data is very informative about $\theta$. The **Cramér-Rao bound** $\mathrm{Var}[\hat{\theta}] \geq 1/\mathcal{F}(\theta)$ sets a hard floor on how accurately any unbiased estimator can recover $\theta$. The **Fisher information matrix** $\bm{F}_{ij}$ generalizes this to vector parameters and defines the geometry of the parameter space, which is what natural gradient descent exploits to take steps that account for the curvature of the loss landscape.
