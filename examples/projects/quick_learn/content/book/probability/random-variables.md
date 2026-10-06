---
topics:
  - "random variable, discrete/continuous, distributions"
  - joint distribution
  - marginalization
  - conditional distribution
  - "key distributions, Bernoulli, Categorical, Gaussian, Multivariate Gaussian, Uniform"
---

# Random Variables, Distributions, and Densities

A **random variable** $X$ is a function from a sample space $\Omega$ to the reals — it's the formal way of saying "a quantity whose value depends on some random outcome." When $X$ can only land on countably many values (heads/tails, number of clicks) we call it **discrete**; when it sweeps out a continuum (temperature, stock price) it's **continuous**. The distinction matters more than it seems: it determines whether you work with sums or integrals, and which kind of probability function describes $X$.

## Probability Functions

For a discrete RV, the **probability mass function** (PMF) $p_X(x) = P(X = x)$ assigns a positive probability to each possible outcome, and they sum to one. For a continuous RV, no single point carries positive probability — instead the **probability density function** (PDF) $f_X(x) \geq 0$ gives you probability by integration: $P(a \leq X \leq b) = \int_a^b f_X(x)\,dx$. The density itself can exceed 1 (a common source of confusion); only the integral over any region is capped at 1.

Both flavors share the **cumulative distribution function** (CDF) $F_X(x) = P(X \leq x)$, a non-decreasing function from 0 to 1. For continuous RVs the PDF is just the derivative of the CDF: $f_X(x) = \frac{d}{dx}F_X(x)$.

## Joint, Marginal, and Conditional Distributions

When two random variables $X$ and $Y$ live on the same probability space, their **joint distribution** describes how they behave together — whether they tend to move in tandem, oppose each other, or act independently. From a joint PMF or PDF you can always recover the **marginal** of one variable by summing (or integrating) out the other:

$$p_X(x) = \sum_y p_{X,Y}(x,y) \qquad \text{or} \qquad f_X(x) = \int f_{X,Y}(x,y)\,dy$$

This is called **marginalization**, and it comes up constantly — every time you want the distribution of one variable without caring about another.

The **conditional distribution** $p_{X|Y}(x|y) = p_{X,Y}(x,y) / p_Y(y)$ tells you the distribution of $X$ once you've observed $Y = y$. **Bayes' theorem** lets you flip the conditioning direction:

$$p_{Y|X}(y|x) = \frac{p_{X|Y}(x|y)\,p_Y(y)}{p_X(x)}$$

This is the engine behind posterior inference: you start with a prior $p_Y(y)$, observe data through the likelihood $p_{X|Y}(x|y)$, and Bayes gives you the posterior.

## Key Distributions

A surprisingly small set of distributions powers most of ML:

- **Bernoulli** $\text{Bern}(p)$: a single coin flip. $P(X=1)=p$, mean $p$, variance $p(1-p)$. Binary classification lives here.
- **Categorical** $\text{Cat}(\mathbf{p})$: the multi-class generalization — a die with $k$ faces, $P(X=i) = p_i$, $\sum p_i = 1$. Softmax outputs parameterize this.
- **Poisson** $\text{Poisson}(\lambda)$: counts of rare events. $P(X=k) = \frac{\lambda^k e^{-\lambda}}{k!}$, with mean and variance both equal to $\lambda$.
- **Uniform** $\text{Uniform}(a,b)$: flat density $\frac{1}{b-a}$ on $[a,b]$. The "I have no idea" distribution.
- **Gaussian** $\mathcal{N}(\mu,\sigma^2)$: the bell curve, $f(x) = \frac{1}{\sqrt{2\pi\sigma^2}}\exp\!\bigl(-\frac{(x-\mu)^2}{2\sigma^2}\bigr)$. Central limit theorem makes this the default choice when you don't have a strong reason to pick something else.
- **Multivariate Gaussian** $\mathcal{N}(\boldsymbol{\mu},\boldsymbol{\Sigma})$: the $k$-dimensional extension, parameterized by a mean vector and covariance matrix. Shows up in Gaussian processes, VAE latent spaces, and anywhere you need a tractable joint distribution over multiple continuous variables.
