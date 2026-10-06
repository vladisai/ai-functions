# Prior

1. Which of the following best describes the relationship between a random variable $X$ and its probability density function $p(x)$?
   - [ ] $p(x) = \mathbb{P}(X = x)$ for all $x$
   - [x] $p(x)$ must satisfy $\int p(x) dx = 1$ and $\mathbb{P}(X \in A) = \int_A p(x) dx$
   - [ ] $p(x)$ is only defined for discrete random variables
   - [ ] $p(x) = F'(x)$ where $F(x)$ is the cumulative distribution function, but only when $X$ is continuous
2. Consider a bivariate random vector $(X, Y)$ with joint density $p(x,y)$. Evaluate these statements about marginalization and conditioning:
   - [T] The marginal density is $p_X(x) = \int p(x,y) dy$
   - [F] If $X$ and $Y$ are independent, then $p(x,y) = p_X(x) + p_Y(y)$
   - [T] The conditional density is $p(y|x) = \frac{p(x,y)}{p_X(x)}$ when $p_X(x) > 0$
   - [T] $\int p(y|x) dy = 1$ for any fixed $x$ where $p_X(x) > 0$
3. Which statement about common probability distributions is correct?
   - [x] A Bernoulli($\mu$) random variable has variance $\mu(1-\mu)$ and takes values in $\{0,1\}$
   - [ ] The multivariate Gaussian $\mathcal{N}(\boldsymbol{\mu}, \boldsymbol{\Sigma})$ has density proportional to $\exp\left(-\frac{1}{2}(\mathbf{x}-\boldsymbol{\mu})^T \boldsymbol{\Sigma} (\mathbf{x}-\boldsymbol{\mu})\right)$
   - [ ] All exponential family distributions have the form $p(x|\boldsymbol{\eta}) = h(x)\exp(\boldsymbol{\eta}^T \mathbf{T}(x))$
   - [ ] The categorical distribution over $K$ categories requires parameters $\boldsymbol{\pi}$ with $\sum_{k=1}^K \pi_k = K$
4. Analyze these statements about independence and conditional independence:
   - [T] If $X \perp\perp Y$ (independent), then $\mathbb{E}[XY] = \mathbb{E}[X]\mathbb{E}[Y]$
   - [F] If $X \perp\perp Y \mid Z$ (conditionally independent given $Z$), then $X \perp\perp Y$ (marginally independent)
   - [T] Independence implies $\text{Cov}[X,Y] = 0$, but zero covariance does not imply independence
   - [T] For three random variables, $X \perp\perp Y \mid Z$ means $p(x,y|z) = p(x|z)p(y|z)$

# Learned
