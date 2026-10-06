Information theory gives us a precise language for uncertainty, surprise, and the gap between two probability distributions. Each quantity below is an *expectation* of something simple. An expectation is a probability-weighted average: if $X$ takes value $x$ with probability $p(x)$, then $\mathbb{E}[f(X)] = \sum_x p(x) f(x)$, or $\int p(x) f(x)\,dx$ for continuous $X$. Keep that in mind and the formulas become much less mysterious.

## Entropy

Start with *surprise*. An event with probability $p$ has surprise $-\log p$: rare events are very surprising, and certain events ($p=1$) have zero surprise. Using $\log_2$ the unit is bits; using $\ln$ it is nats.

**Shannon entropy** is the average surprise of a discrete random variable $X$:

$$\mathrm{H}(X) = -\sum_x p(x)\log p(x).$$

Example: a fair coin has $\mathrm{H} = -2\cdot\tfrac12\log_2\tfrac12 = 1$ bit. A coin that lands heads with probability $0.99$ has $\mathrm{H} = -0.99\log_2 0.99 - 0.01\log_2 0.01 \approx 0.08$ bits. You're rarely surprised, so there is little uncertainty. High entropy means spread out and unpredictable; low entropy means concentrated. For a fixed set of outcomes, the uniform distribution has the maximum entropy. This is the same flavor of idea as entropy in statistical mechanics, which has the same formula up to a constant.

**Differential entropy** replaces the sum with an integral: $h(X) = -\int p(x)\log p(x)\,dx$. Here $p(x)$ is a density, which can exceed 1, so $h$ can be negative. For example, a uniform density on $[0, \tfrac12]$ equals $2$ there, and $h = -\log 2 < 0$. It is not the limit of discrete entropy, and it changes if you rescale $x$. Treat it as a useful quantity, but not as "bits needed to encode."

## KL Divergence

The **KL divergence** is the expected log-ratio of two distributions, with the expectation taken under $p$:

$$\mathrm{KL}(p\|q) = \mathbb{E}_p\!\left[\log\frac{p(X)}{q(X)}\right] = \sum_x p(x)\log\frac{p(x)}{q(x)}.$$

It measures the extra surprise you incur by believing $q$ when the truth is $p$.

**Non-negativity** (Gibbs' inequality): $\mathrm{KL}(p\|q)\ge 0$, with equality only when $p=q$. A quick argument: since $\ln t \le t-1$, we get $-\mathrm{KL} = \mathbb{E}_p[\ln\frac{q}{p}] \le \mathbb{E}_p[\frac{q}{p}-1] = \sum_x q(x) - 1 = 0$.

**Asymmetry**: in general $\mathrm{KL}(p\|q)\ne\mathrm{KL}(q\|p)$. Take $p=(1/2,1/2)$ and $q=(1,0)$ on two outcomes. Then $\mathrm{KL}(q\|p)=\ln 2$, but $\mathrm{KL}(p\|q)=\infty$, because $p$ puts mass where $q$ says it's impossible. So KL is not a distance. The direction matters in practice:

- Forward KL, $\mathrm{KL}(p\|q)$, punishes $q$ for missing regions where $p$ has mass. It is *mode-covering*.
- Reverse KL, $\mathrm{KL}(q\|p)$, punishes $q$ for putting mass where $p$ has little. It is *mode-seeking*, and it is the one used in variational inference.

## Cross-Entropy

$$\mathrm{H}(p,q) = -\mathbb{E}_p[\log q(X)] = \mathrm{H}(p)+\mathrm{KL}(p\|q).$$

This is the average log-loss when data come from $p$ but your model says $q$. The identity follows by splitting $-\log q = -\log p + \log\frac{p}{q}$ inside the expectation. Since $\mathrm{H}(p)$ doesn't depend on the model $q$, minimizing cross-entropy is the same as minimizing KL. With a dataset, the average of $-\log q(x_i)$ over samples approximates $\mathrm{H}(p,q)$, so this is also *negative log-likelihood*. That's why cross-entropy is the standard classification loss.

## Mutual Information

$$I(X;Y)=\mathrm{KL}\big(p(x,y)\,\|\,p(x)p(y)\big)=\mathrm{H}(X)-\mathrm{H}(X|Y).$$

The first form compares the true joint distribution to what it would be if $X$ and $Y$ were independent (the product of marginals). The second says: how much does knowing $Y$ reduce uncertainty about $X$? It is symmetric, non-negative (it's a KL), and zero exactly when $X$ and $Y$ are independent. Unlike correlation, it detects any dependence, not just linear. For instance, $Y=X^2$ with $X$ symmetric about 0 has zero correlation but positive mutual information.

Two useful tools: the **chain rule** $\mathrm{H}(X,Y)=\mathrm{H}(X)+\mathrm{H}(Y|X)$, and **conditional mutual information** $I(X;Y|Z)=\mathrm{H}(X|Z)-\mathrm{H}(X|Y,Z)$. They appear in information bottleneck methods and feature selection.

## Fisher Information

Suppose a model $p(x;\theta)$ has a parameter $\theta$. The derivative $\frac{\partial}{\partial\theta}\log p(x;\theta)$ (the *score*) says how strongly the log-likelihood reacts to $\theta$. **Fisher information** is its mean square:

$$\mathcal{F}(\theta)=\mathbb{E}\!\left[\left(\tfrac{\partial}{\partial\theta}\log p(X;\theta)\right)^2\right].$$

Under mild regularity conditions it equals $-\mathbb{E}\big[\tfrac{\partial^2}{\partial\theta^2}\log p(X;\theta)\big]$, the expected *curvature* of the log-likelihood. A sharply peaked likelihood means the data pin down $\theta$ well. It is also the local curvature of KL: for small $\delta$, $\mathrm{KL}(p_\theta\|p_{\theta+\delta})\approx\tfrac12\mathcal{F}(\theta)\delta^2$.

The **Cramér-Rao bound** makes this precise: any unbiased estimator satisfies $\mathrm{Var}[\hat\theta]\ge 1/\mathcal{F}(\theta)$.

For a parameter vector, the **Fisher information matrix** $F_{ij}=\mathbb{E}[\partial_i\log p\;\partial_j\log p]$ is symmetric and positive semi-definite, like the Hessian of a quadratic. It defines a geometry on parameter space, which **natural gradient descent** uses by preconditioning the gradient with $F^{-1}$.
