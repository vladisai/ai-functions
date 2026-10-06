<!-- note: Added a short independence discussion, since you missed the independence and conditional independence question. -->
A **random variable** is a number that depends on the outcome of something random. Roll a die and record the face, measure the time between two detector clicks, or flip a coin and write 1 for heads and 0 for tails. Each is a random variable. Formally, if $\Omega$ is the set of all possible outcomes (the *sample space*), a random variable $X$ is a function $X:\Omega\to\mathbb{R}$ that assigns a number to each outcome. We usually suppress $\Omega$ and just ask how likely $X$ is to take various values.

Random variables come in two flavors:

- **Discrete**: $X$ takes countably many values (coin flips, die rolls, number of clicks). You work with sums.
- **Continuous**: $X$ sweeps out a continuum (temperature, a particle's position). You work with integrals.

The list of which values $X$ takes and how likely each is makes up its **distribution**.

## Probability Functions

For a discrete $X$, the **probability mass function** (PMF) is $p_X(x) = P(X = x)$. Each value is non-negative and they sum to one: $\sum_x p_X(x) = 1$.

For a continuous $X$, the probability of hitting any exact point is zero, just as a single point in a rod has zero mass. What exists is a **probability density function** (PDF) $f_X(x)\ge 0$, which plays the role of mass per unit length. Probability comes from integrating:

$$P(a \le X \le b) = \int_a^b f_X(x)\,dx, \qquad \int_{-\infty}^{\infty} f_X(x)\,dx = 1.$$

A density is *not* a probability, so it can exceed 1. Example: let $X$ be uniform on $[0, \tfrac12]$. Then $f_X(x)=2$ on that interval, yet the total area is $2\times\tfrac12=1$.

The **cumulative distribution function** (CDF) $F_X(x)=P(X\le x)$ works for both kinds. It is non-decreasing, going from 0 to 1. For continuous $X$, $f_X(x)=\frac{d}{dx}F_X(x)$.

## Joint, Marginal, and Conditional Distributions

When two random variables $X$ and $Y$ come from the same experiment, their **joint distribution** $p_{X,Y}(x,y)$ (or density $f_{X,Y}$) describes them together, including any correlation. Think of it as a landscape over the $(x,y)$ plane with total volume 1.

Suppose $X$ is today's weather and $Y$ is whether you bring an umbrella:

| | $Y$=umbrella | $Y$=none |
|---|---|---|
| $X$=rain | 0.25 | 0.05 |
| $X$=sun | 0.10 | 0.60 |

**Marginalization** recovers the distribution of one variable by summing (or integrating) out the other:

$$p_X(x) = \sum_y p_{X,Y}(x,y) \qquad\text{or}\qquad f_X(x) = \int f_{X,Y}(x,y)\,dy.$$

Here $P(\text{rain}) = 0.25+0.05 = 0.30$. It is like collapsing a 2D density onto one axis.

The **conditional distribution** restricts attention to the slice where $Y=y$ and renormalizes it:

$$p_{X|Y}(x|y) = \frac{p_{X,Y}(x,y)}{p_Y(y)}.$$

Given an umbrella, $P(\text{rain}\mid\text{umbrella}) = 0.25/0.35 \approx 0.71$. Dividing by $p_Y(y)$ makes the slice sum to one again.

Writing the joint both ways, $p_{X,Y}=p_{X|Y}\,p_Y=p_{Y|X}\,p_X$, gives **Bayes' theorem**:

$$p_{Y|X}(y|x) = \frac{p_{X|Y}(x|y)\,p_Y(y)}{p_X(x)}.$$

### Independence and conditional independence

$X$ and $Y$ are **independent** if the joint factorizes: $p_{X,Y}=p_X\,p_Y$ (a product, not a sum). Then $\mathbb{E}[XY]=\mathbb{E}[X]\mathbb{E}[Y]$, so the covariance is zero. The converse fails: zero covariance does not imply independence.

They are **conditionally independent given $Z$** if
$$p(x,y|z)=p(x|z)\,p(y|z).$$
This does *not* imply ordinary independence. Example: $Z$ is a randomly chosen coin, fair or heavily biased, and $X$, $Y$ are two flips of it. Given $Z$, the flips are independent. Marginally they are not, because seeing $X$=heads makes the biased coin more likely, which raises the chance that $Y$ is heads. The reverse also fails: independent variables can become dependent once you condition on a third.

## Key Distributions

- **Bernoulli** $\text{Bern}(p)$: one coin flip. $P(X=1)=p$, mean $p$, variance $p(1-p)$.
- **Categorical** $\text{Cat}(\mathbf{p})$: a $k$-sided die with $P(X=i)=p_i$ and $\sum_i p_i=1$. Softmax outputs in classifiers are categorical parameters.
- **Uniform** $\text{Uniform}(a,b)$: constant density $\frac{1}{b-a}$ on $[a,b]$, the "no preference" distribution.
- **Gaussian** $\mathcal{N}(\mu,\sigma^2)$: the bell curve,
$$f(x)=\frac{1}{\sqrt{2\pi\sigma^2}}\exp\!\Bigl(-\frac{(x-\mu)^2}{2\sigma^2}\Bigr).$$
$\mu$ is the center and $\sigma$ the width. It appears everywhere because sums of many small independent effects tend toward it (the central limit theorem, covered later).
- **Multivariate Gaussian** $\mathcal{N}(\boldsymbol{\mu},\boldsymbol{\Sigma})$ in $k$ dimensions:
$$f(\mathbf{x})=\frac{1}{\sqrt{(2\pi)^k\det\boldsymbol{\Sigma}}}\exp\!\Bigl(-\tfrac12(\mathbf{x}-\boldsymbol{\mu})^\top\boldsymbol{\Sigma}^{-1}(\mathbf{x}-\boldsymbol{\mu})\Bigr).$$
$\boldsymbol{\mu}$ is the center and $\boldsymbol{\Sigma}$ is a symmetric positive-definite covariance matrix. Note the *inverse* $\boldsymbol{\Sigma}^{-1}$ in the exponent. Its eigenvectors give the principal axes of the elliptical level sets, and its eigenvalues give the variances along them. Diagonal entries are the individual variances, and off-diagonal entries measure how coordinates vary together.
