Expectation is the first thing to learn about a random variable, and it will feel familiar if you have seen a center of mass or an average over a distribution. Everything here builds on integrals and sums you already know.

<!-- note: Added intuition and a worked example, since you're new to probability but strong in calculus. -->
## Expectation and Linearity

A random variable $X$ is a quantity whose value is determined by a random outcome, and its distribution says how likely each value is. The **expectation** $\mathbb{E}[X]$ is the probability-weighted average of the values:

$$\mathbb{E}[X] = \sum_x x\,p(x) \quad\text{(discrete)}, \qquad \mathbb{E}[X] = \int x\,f(x)\,dx \quad\text{(continuous)}.$$

Here $p(x)$ is the probability of each value and $f(x)$ is the probability density. The formula is the same as a center of mass, with probability playing the role of mass. It answers: "if I sampled $X$ over and over, what would the long-run average be?"

For a fair six-sided die, $\mathbb{E}[X] = \tfrac16(1+2+\dots+6) = 3.5$. Note that 3.5 is never actually rolled. The expectation is an average, not a likely value.

The same idea applies to functions of $X$: $\mathbb{E}[g(X)] = \sum_x g(x)p(x)$, or $\int g(x) f(x)\,dx$.

**Linearity** says $\mathbb{E}[aX + bY] = a\mathbb{E}[X] + b\mathbb{E}[Y]$. It holds *regardless* of whether $X$ and $Y$ are dependent. This follows because sums and integrals are linear. For two dice, $\mathbb{E}[X+Y] = 7$ whether or not the dice influence each other. This is powerful because you can compute the expected value of a complicated sum term by term, without tracking correlations.

<!-- note: Explained variance as spread, with a physics-flavored link to your linear algebra. -->
## Variance and Covariance

**Variance** measures spread around the mean:

$$\text{Var}[X] = \mathbb{E}[(X - \mathbb{E}[X])^2] = \mathbb{E}[X^2] - (\mathbb{E}[X])^2.$$

It is the average squared deviation, like a moment of inertia about the mean. The second form follows by expanding the square and using linearity. Its square root is the **standard deviation** $\sigma$, which has the same units as $X$.

Variance is not linear: $\text{Var}[aX] = a^2\text{Var}[X]$, and adding a constant changes nothing. For a sum, the general rule is

$$\text{Var}[X+Y] = \text{Var}[X] + \text{Var}[Y] + 2\,\text{Cov}[X,Y].$$

If $X$ and $Y$ are independent (knowing one tells you nothing about the other), the covariance term vanishes and variances simply add.

**Covariance** $\text{Cov}[X,Y] = \mathbb{E}[(X-\mathbb{E}X)(Y-\mathbb{E}Y)] = \mathbb{E}[XY] - \mathbb{E}[X]\mathbb{E}[Y]$ captures how two variables move together. It is positive if they tend to rise together, negative if one rises when the other falls, and zero if they are *linearly* unrelated. Independent variables have zero covariance, but zero covariance does not imply independence. For example, if $X$ is symmetric about 0 and $Y = X^2$, then $\text{Cov}[X,Y]=0$ even though $Y$ is completely determined by $X$.

Dividing by the standard deviations gives the **correlation** $\rho = \text{Cov}[X,Y]/(\sigma_X\sigma_Y)\in[-1,1]$, which is dimensionless.

For a random vector $\mathbf{X}=(X_1,\dots,X_n)$, the **covariance matrix** has entries $\Sigma_{ij}=\text{Cov}[X_i,X_j]$. It is symmetric and positive semi-definite, so your linear algebra applies directly: its eigenvectors are the directions of independent variation, and its eigenvalues are the variances along them. This is exactly what PCA computes, and $\Sigma$ also parameterizes multivariate Gaussians.

<!-- note: Added a concrete example for the tower property and total variance. -->
## Conditional Expectations

$\mathbb{E}[X\mid Y]$ is the average of $X$ given that you know $Y$. It depends on $Y$, so it is itself a random variable.

The **tower property** (law of iterated expectations) says

$$\mathbb{E}[X] = \mathbb{E}\big[\mathbb{E}[X\mid Y]\big].$$

You can compute an average by first averaging within each group defined by $Y$, then averaging those group means, weighted by how likely each group is. For example, suppose 60% of a class is in group A with mean score 70, and 40% is in group B with mean score 80. Then the overall mean is $0.6\cdot70 + 0.4\cdot80 = 74$.

The **law of total variance** splits spread into two parts:

$$\text{Var}[X] = \mathbb{E}\big[\text{Var}[X\mid Y]\big] + \text{Var}\big[\mathbb{E}[X\mid Y]\big].$$

The first term is the average spread *within* groups. The second is the spread of the group means *between* groups. In the class example, the second term is $0.6(70-74)^2 + 0.4(80-74)^2 = 24$. If the within-group variance averages 100, the total variance is 124. This decomposition is the same partition of sums of squares used in ANOVA, and it appears often in derivations about estimators and noisy models.
