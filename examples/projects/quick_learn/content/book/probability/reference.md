---
title: "Probability and Statistics Primer - Core Material"
type: core_material
---

## Random Variables and Distributions

A random variable is a quantity whose value is not known to us. This could be because the quantity pertains to some future phenomenon (like the outcome of a coin toss), or because it has been measured with an imperfect instrument (like the temperature at 8AM yesterday). How can we reason about such a quantity if we do not know its value?

Since the value is unknown, we can instead consider all possible values that the variable can take, and describe our uncertainty by assigning a probability to each of them. Then, instead of manipulating values, for instance with algebraic operations, we can manipulate their probabilities. That is the purpose of probability theory. Except that in some cases every individual value may have zero probability, so any algebraic manipulation of individual probabilities would be moot. For instance, the temperature yesterday could have taken any value in the continuum between, say, 0 and 100 degrees Celsius. There are uncountably many possible values in that finite interval, and it makes no sense to assign a finite probability to any single one of them: even if the temperature happened to be precisely $\sqrt{2}$ degrees Celsius, no instrument could ever confirm it, as doing so would require infinite precision.

So, in probability theory we need to consider not just the individual values that a variable can take, but *collections* of possible values, or "event,"  for instance the event that the temperature was between 24 and 25 degrees. To do this consistently, we need a structured way of describing  which collections of values are eligible to receive a probability. Not every conceivable collection needs to qualify, but the eligible ones must be closed under the operations we expect of events, like exclusion (if $A$ is an eligible event, then so is "not $A$") or alternatives (if $A_1, A_2, \ldots$ are eligible, then so is  "$A_1$ or $A_2$ or $\ldots$"). The collection of all eligible events is called a *$\sigma$-algebra*. It is typically swept under the rug in introductory  courses, yet it is precisely what makes probability theory work: it tells us which questions of the form "what is the probability something happening?"\ are  guaranteed to have an answer.

A random variable, then, is a function from experimental outcomes to
numerical values with the following essential property: for every eligible set of values (in the $\sigma$-algebra), the
set of outcomes that maps into it is itself an eligible event; that is, an event to which we can assign or {\em measure} the probability. Such a function is called *measurable*. If the function was not measurable, there would be sets of values for which the question "what is the probability of the value landing in that set?"\ has no answer, and  any hope of reasoning under uncertainty would vanish.

Probability theory has been developed to extend the operations we routinely perform on known quantities, such as addition, multiplication, comparison, optimization, to such measurable functions, which are called  *random variables*. It is confusing to call variables functions, but you  get used to it. Once we know how to manipulate random variables algebraically, we can perform *inference*: given partial observations (for instance, a noisy measurement), we can update our description of the unknown and make
principled statements about what values it is likely to take.

> **Definition (Random variable)**
> A *random variable* is a measurable function $X\colon \Omega \to \mathcal{X}$ from a sample space $\Omega$ (the space of events, equipped with a $\sigma$-algebra $\mathcal{F}$ and a probability measure $\mathbb{P}$) to a measurable space $\mathcal{X}$.  When $\mathcal{X}$ is countable, $X$ is *discrete*; when $\mathcal{X} \subseteq \mathbb{R}^d$, $X$ is *continuous* (assuming a density exists with respect to Lebesgue measure).

For a discrete random variable, the *probability mass function* (pmf) is

$$p(x)  =  \mathbb{P}(X = x),  \sum_{x \in \mathcal{X}} p(x) = 1.$$

For a continuous random variable, the *probability density function* (pdf) $p(x)$ satisfies

$$\mathbb{P}(X \in A)  =  \int_{A} p(x) dx,  \int_{\mathcal{X}} p(x) dx = 1.$$

In both cases the *cumulative distribution function* (cdf) is $F(x) = \mathbb{P}(X \le x)$.

### Examples

We catalogue the distributions that appear most frequently in subsequent chapters.

#### Bernoulli and categorical.
A binary outcome $X \in \{0,1\}$ with $\mathbb{P}(X=1) = \mu$ is written $X \sim \mathrm{Bern}(\mu)$.  The generalization to $K$ categories is the categorical (or multinoulli) distribution:

$$X \sim \mathrm{Cat}(\bm{\pi}),  \mathbb{P}(X = k) = \pi_k,  \sum_{k=1}^{K}\pi_k = 1.$$

> **Relevance to AI: Language Models**
> Every autoregressive language model produces, at each time step, a categorical distribution over a vocabulary of $K$ tokens.  The vector $\bm{\pi}$ is the output of a softmax layer: $\pi_k = \exp(z_k)/\sum_j \exp(z_j)$, where $\bm{z}$ are the logits.  Understanding the categorical distribution is thus essential for understanding next-token prediction, beam search, and nucleus (top-$p$) sampling.

#### Gaussian (normal).
A continuous random variable $X \sim \mathcal{N}(\mu, \sigma^2)$ has density

$$p(x) = \frac{1}{\sqrt{2\pi\sigma^2}}\exp\Bigl(-\frac{(x-\mu)^2}{2\sigma^2}\Bigr).$$

The multivariate generalization $\bm{X} \sim \mathcal{N}(\bm{\mu}, \bm{\Sigma})$ in $\mathbb{R}^d$ has density

$$p(\bm{x}) = \frac{1}{(2\pi)^{d/2}|\bm{\Sigma}|^{1/2}}\exp\Bigl(-\tfrac{1}{2}(\bm{x}-\bm{\mu})^\top\bm{\Sigma}^{-1}(\bm{x}-\bm{\mu})\Bigr).$$

> **Relevance to AI: Deep Learning**
> Weight initialization, Gaussian noise for exploration in policy-gradient methods, the reparameterization trick in variational autoencoders, and diffusion models all rely on the multivariate Gaussian.  The log-density being quadratic in $\bm{x}$ makes gradient computation particularly clean.

#### Exponential family.
Many of the distributions we encounter belong to the *exponential family*:

$$
  p(x \mid \bm{\eta}) = h(x)\exp\bigl(\bm{\eta}^\top \bm{T}(x) - A(\bm{\eta})\bigr),$$

where $\bm{\eta}$ are the *natural parameters*, $\bm{T}(x)$ the *sufficient statistics*, and $A(\bm{\eta})$ the *log-partition function*.  Bernoulli, categorical, Gaussian, Poisson, and gamma distributions are all members.  A key property is that gradients of $A$ give the cumulants:

$$\nabla_{\bm{\eta}} A(\bm{\eta}) = \mathbb{E}[\bm{T}(X)],  \nabla^2_{\bm{\eta}} A(\bm{\eta}) = \mathrm{Cov}[\bm{T}(X)].$$

This makes maximum-likelihood estimation particularly tractable: the MLE sets the expected sufficient statistics equal to their empirical averages.

## Expectation

> **Definition (Expectation)**
> The *expectation* (or *expected value*) of a function $g(X)$ of a random variable $X$ is

$$\mathbb{E}[g(X)] = \begin{cases}
    \displaystyle\sum_{x} g(x) p(x) & \text{(discrete)},\\[6pt]
    \displaystyle\int g(x) p(x) dx & \text{(continuous)}.
  \end{cases}$$

#### Linearity.  For any constants $a$, $b$ and random variables $X$, $Y$:

$$
  \mathbb{E}[aX + bY] = a\mathbb{E}[X] + b\mathbb{E}[Y].$$

This holds regardless of whether $X$ and $Y$ are independent.

> **Definition (Variance and covariance)**
>

$$\mathrm{Var}[X] = \mathbb{E}\bigl[(X - \mathbb{E}[X])^2\bigr] = \mathbb{E}[X^2] - (\mathbb{E}[X])^2.$$

For two random variables:

$$\mathrm{Cov}[X,Y] = \mathbb{E}\bigl[(X - \mathbb{E}[X])(Y - \mathbb{E}[Y])\bigr] = \mathbb{E}[XY] - \mathbb{E}[X]\mathbb{E}[Y].$$

> **Proposition (Variance of a linear combination)**
>
For constants $a_1,\ldots,a_n$ and random variables $X_1,\ldots,X_n$,

$$\mathrm{Var}\Biggl[\sum_{i=1}^{n} a_i X_i\Biggr]
  = \sum_{i=1}^{n} a_i^2 \mathrm{Var}[X_i]
    + 2\sum_{1 \le i < j \le n} a_i a_j \mathrm{Cov}[X_i,X_j].$$

If the $X_i$ are mutually uncorrelated, the cross terms vanish and $\mathrm{Var}[\sum a_i X_i] = \sum a_i^2 \mathrm{Var}[X_i]$.

### Important Inequalities

> **Theorem (Jensen's inequality)**
>
If $\varphi$ is a convex function and $X$ is a random variable with $\mathbb{E}[|X|] < \infty$, then

$$
  \varphi\bigl(\mathbb{E}[X]\bigr)  \le  \mathbb{E}\bigl[\varphi(X)\bigr].$$

Equality holds if and only if $\varphi$ is affine on the support of $X$ (or $X$ is constant a.s.).

> *Proof*
> Since $\varphi$ is convex, for every point $\mu = \mathbb{E}[X]$ there exists a supporting hyperplane: a constant $\lambda$ such that $\varphi(x) \ge \varphi(\mu) + \lambda(x - \mu)$ for all $x$.  Taking expectations of both sides:

$$\mathbb{E}[\varphi(X)]  \ge  \varphi(\mu) + \lambda \mathbb{E}[X - \mu] = \varphi(\mu) = \varphi\bigl(\mathbb{E}[X]\bigr). $$

 ∎

> **Relevance to AI: Variational Inference and the ELBO**
> Jensen's inequality takes different names in different contexts, from the *evidence lower bound* (ELBO) used in variational autoencoders (VAEs) to the expectation--maximization (EM) algorithm.  Because $\log$ is concave, Jensen gives $\log\mathbb{E}[X] \ge \mathbb{E}[\log X]$ (reversed inequality), which yields a tractable lower bound on the intractable log-marginal-likelihood $\log p(\bm{x})$.

> **Theorem (Markov's inequality)**
> For a non-negative random variable $X$ and $a > 0$:

$$\mathbb{P}(X \ge a)  \le  \frac{\mathbb{E}[X]}{a}.$$

> **Corollary (Chebyshev's inequality)**
> For any random variable $X$ with finite mean and variance, and $k > 0$:

$$\mathbb{P}\bigl(|X - \mathbb{E}[X]| \ge k\bigr)  \le  \frac{\mathrm{Var}[X]}{k^2}.$$

> **Theorem (Hoeffding's inequality)**
>
Let $X_1,\ldots,X_n$ be independent random variables with $a_i \le X_i \le b_i$ almost surely.  Let $\bar{X} = \frac{1}{n}\sum_{i=1}^n X_i$.  Then for any $t > 0$:

$$\mathbb{P}\bigl(\bar{X} - \mathbb{E}[\bar{X}] \ge t\bigr)  \le  \exp\biggl(-\frac{2n^2 t^2}{\sum_{i=1}^n (b_i - a_i)^2}\biggr).$$

> **Relevance to AI: Exploration Bounds in Bandits and RL**
> Hoeffding's inequality is the workhorse behind the analysis of upper confidence bound (UCB) algorithms for multi-armed bandits.  It provides finite-sample concentration guarantees that translate into regret bounds.  More broadly, concentration inequalities underpin PAC (probably approximately correct) learning theory.

### The Law of Large Numbers and Central Limit Theorem

> **Theorem (Strong law of large numbers)**
> Let $X_1, X_2, \ldots$ be i.i.d.\ with $\mathbb{E}[|X_1|] < \infty$.  Then

$$\bar{X}_n = \frac{1}{n}\sum_{i=1}^{n} X_i  \xrightarrow{\text{a.s.}}  \mathbb{E}[X_1]  \text{as } n \to \infty.$$

> **Theorem (Central limit theorem)**
>
Let $X_1, X_2, \ldots$ be i.i.d.\ with mean $\mu$ and variance $\sigma^2 \in (0,\infty)$.  Then

$$\sqrt{n} \frac{\bar{X}_n - \mu}{\sigma}  \xrightarrow{d}  \mathcal{N}(0,1)  \text{as } n \to \infty.$$

> **Relevance to AI: Monte Carlo Methods in RL**
> The law of large numbers justifies every Monte Carlo estimate in machine learning: from stochastic gradient descent (SGD), which replaces a full-data gradient with a sample average, to Monte Carlo policy evaluation in reinforcement learning, which estimates a value function by averaging returns.  The CLT tells us the rate: estimation error decreases as $O(1/\sqrt{n})$.

## Conditioning and Independence



### Conditional Probability and Bayes' Theorem

> **Definition (Conditional probability)**
> For events $A$, $B$ with $\mathbb{P}(B) > 0$:

$$\mathbb{P}(A \mid B) = \frac{\mathbb{P}(A \cap B)}{\mathbb{P}(B)}.$$

> **Theorem (Bayes' theorem)**
>

$$
  p(\bm{\theta} \mid \bm{x}) = \frac{p(\bm{x} \mid \bm{\theta}) p(\bm{\theta})}{p(\bm{x})},
   p(\bm{x}) = \int p(\bm{x} \mid \bm{\theta}) p(\bm{\theta}) d\bm{\theta}.$$

Here $p(\bm{\theta})$ is the *prior*, $p(\bm{x}\mid\bm{\theta})$ is the *likelihood*, $p(\bm{\theta}\mid\bm{x})$ is the *posterior*, and $p(\bm{x})$ is the *evidence* (or marginal likelihood).

> **Relevance to AI: Bayesian Learning and RLHF**
> Bayes' theorem is the foundation of Bayesian inference: given a prior belief over model parameters and observed data, we update to a posterior.  In the context of AI agents, Bayesian updating appears in belief-state MDPs (POMDPs), Thompson sampling for exploration, and as the conceptual framework behind reward modeling in RLHF (reinforcement learning from human feedback), where the posterior over reward functions is conditioned on human preference data.

### The Law of Total Expectation and Total Variance

> **Theorem (Law of total expectation (tower property))**
>
For random variables $X$ and $Y$:

$$
  \mathbb{E}[X] = \mathbb{E}\bigl[\mathbb{E}[X \mid Y]\bigr].$$

More generally, $\mathbb{E}[X \mid Z] = \mathbb{E}\bigl[\mathbb{E}[X \mid Y, Z] \big| Z\bigr]$.

> *Proof*
> In the continuous case:

$$\mathbb{E}\bigl[\mathbb{E}[X \mid Y]\bigr]
  = \int \Bigl(\int x p(x \mid y) dx\Bigr) p(y) dy
  = \int\int x p(x,y) dx dy = \mathbb{E}[X]. $$

 ∎

> **Theorem (Law of total variance)**
>

$$
  \mathrm{Var}[X] = \mathbb{E}\bigl[\mathrm{Var}[X \mid Y]\bigr] + \mathrm{Var}\bigl[\mathbb{E}[X \mid Y]\bigr].$$

> **Relevance to AI: Variance Reduction and Baselines**
> The law of total variance decomposes overall uncertainty into "within-group" and "between-group" components.  In policy-gradient methods, this decomposition motivates the use of *baselines* to reduce the variance of gradient estimators: $\mathrm{Var}[\nabla \log \pi(a|s)(R - b)]$ is minimized by choosing the baseline $b$ that minimizes $\mathrm{Var}[\mathbb{E}[\cdot \mid s]]$.

### Independence and Conditional Independence

> **Definition (Independence)**
> Random variables $X$ and $Y$ are *independent*, written $X \perp\perp Y$, if

$$p(x, y) = p(x) p(y)  \text{for all } x, y.$$

Equivalently, $\mathbb{P}(X \in A, Y \in B) = \mathbb{P}(X \in A) \mathbb{P}(Y \in B)$ for all measurable sets $A,B$.

> **Definition (Conditional independence)**
> $X$ and $Y$ are *conditionally independent given* $Z$, written $X \perp\perp Y \mid Z$, if

$$p(x, y \mid z) = p(x \mid z) p(y \mid z)  \text{for all } x, y, z.$$

> **Remark**
> Independence does not imply conditional independence, nor vice versa.  This subtlety is central to graphical models: in a na\"ive Bayes classifier, features $X_1,\ldots,X_d$ are conditionally independent given the class label $Y$, yet marginally they may be highly correlated.

> **Relevance to AI: The Markov Property and Graphical Models**
> The Markov property () is a conditional independence statement: the future is independent of the past given the present.  Conditional independence is also the key structural assumption in Bayesian networks, hidden Markov models (HMMs), and the factored state representations used in model-based RL.

### Exchangeability and the Bayesian Perspective

> **Definition (Exchangeability)**
> A finite sequence $X_1,\ldots,X_n$ is *exchangeable* if for every permutation $\sigma$ of $\{1,\ldots,n\}$:

$$p(x_1,\ldots,x_n) = p(x_{\sigma(1)},\ldots,x_{\sigma(n)}).$$

An infinite sequence $X_1, X_2, \ldots$ is exchangeable if every finite subsequence is exchangeable.

Every i.i.d.\ sequence is exchangeable, but exchangeability is strictly weaker: it allows dependence between the $X_i$, as long as the joint distribution is permutation-invariant.

> **Theorem (de Finetti's theorem)**
>
If $X_1, X_2, \ldots$ is an infinite exchangeable sequence of $\{0,1\}$-valued random variables, then there exists a probability measure $\mu$ on $[0,1]$ such that

$$
  p(x_1,\ldots,x_n) = \int_0^1 \prod_{i=1}^{n} \theta^{x_i}(1-\theta)^{1-x_i} d\mu(\theta).$$

More generally, for exchangeable real-valued sequences, there exists a random probability measure $\Theta$ such that, conditional on $\Theta = \theta$, the $X_i$ are i.i.d.\ with distribution $\theta$.

> *Proof (Proof sketch)*
> Define $\bar{X}_n = n^{-1}\sum_{i=1}^n X_i$.  By exchangeability and the strong law of large numbers, $\bar{X}_n \to \Theta$ a.s.\ for some random variable $\Theta \in [0,1]$.  Conditional on $\Theta = \theta$, the conditional distribution of any finite subset $(X_{i_1},\ldots,X_{i_k})$ converges to the product $\prod_j \theta^{x_{i_j}}(1-\theta)^{1-x_{i_j}}$.  The measure $\mu$ is the distribution of $\Theta$.  A rigorous proof uses the Hewitt--Savage zero--one law; see, e.g., Schervish (1995). ∎

> **Remark**
> De Finetti's theorem provides a deep justification for Bayesian modeling.  If we believe our data are exchangeable (but not necessarily independent), then there must exist a latent parameter $\Theta$ with a prior distribution $\mu$ such that, conditional on $\Theta$, the data are i.i.d.  The "prior" is not a subjective choice---it is forced by the structural assumption of exchangeability.

> **Relevance to AI: Why Exchangeability Matters for AI**
> The assumption that training examples are "drawn i.i.d.\ from some distribution" is the standard setup in supervised learning, but it is stronger than necessary.  De Finetti's theorem shows that exchangeability suffices and naturally leads to the Bayesian framework.  This perspective is crucial for understanding Bayesian neural networks, meta-learning (where tasks are exchangeable), and in-context learning in large language models---where the model's behavior on a prompt can be interpreted as implicit Bayesian inference over a latent concept given exchangeable examples.

## Random Processes and Markov Chains



### Stochastic Processes

> **Definition (Stochastic process)**
> A *stochastic process* is a collection of random variables $\{X_t\}_{t \in \mathcal{T}}$ defined on a common probability space, indexed by a set $\mathcal{T}$ (typically $\mathbb{N}$ for discrete time or $[0,\infty)$ for continuous time).

### Markov Chains

> **Definition (Markov property)**
> A discrete-time stochastic process $(X_0, X_1, X_2, \ldots)$ taking values in a countable state space $\mathcal{S}$ is a *Markov chain* if for all $t \ge 0$ and all states $s_0,\ldots,s_{t+1}$:

$$
  \mathbb{P}(X_{t+1} = s_{t+1} \mid X_t = s_t, X_{t-1} = s_{t-1}, \ldots, X_0 = s_0)
  = \mathbb{P}(X_{t+1} = s_{t+1} \mid X_t = s_t).$$

When the right-hand side does not depend on $t$, the chain is *time-homogeneous*, and we write the *transition matrix* $\bm{P}$ with entries $P_{ij} = \mathbb{P}(X_{t+1} = j \mid X_t = i)$.

> **Remark**
> The Markov property states: *the future is independent of the past, given the present.*  Formally, $X_{t+1} \perp\perp X_{0:t-1} \mid X_t$.  This is precisely the conditional independence structure of  applied to temporal sequences.

### Stationary Distributions and Ergodicity

> **Definition (Stationary distribution)**
> A distribution $\bm{\pi}$ over $\mathcal{S}$ is a *stationary distribution* (or *invariant measure*) of a Markov chain with transition matrix $\bm{P}$ if

$$\bm{\pi}^\top \bm{P} = \bm{\pi}^\top,
   \text{i.e., } \pi_j = \sum_{i \in \mathcal{S}} \pi_i P_{ij}   \forall  j.$$

> **Definition (Irreducibility and aperiodicity)**
> A Markov chain is *irreducible* if every state can be reached from every other state in a finite number of steps.  It is *aperiodic* if the greatest common divisor of the set of return times to any state is 1.

> **Theorem (Fundamental theorem of Markov chains)**
>
If a Markov chain on a finite state space is irreducible and aperiodic, then:

- A unique stationary distribution $\bm{\pi}$ exists.
  - For any initial distribution, $\mathbb{P}(X_t = j) \to \pi_j$ as $t \to \infty$.
  - The time-average converges: $\frac{1}{T}\sum_{t=0}^{T-1}\mathbf{1}[X_t = j] \xrightarrow{\text{a.s.}} \pi_j$.

> **Definition (Detailed balance)**
> A distribution $\bm{\pi}$ satisfies *detailed balance* with respect to $\bm{P}$ if

$$
  \pi_i P_{ij} = \pi_j P_{ji}  \text{for all } i, j.$$

A chain satisfying detailed balance is called *reversible*.  Detailed balance implies $\bm{\pi}$ is stationary (sum both sides over $i$).

> **Relevance to AI: MCMC and Diffusion Models**
> Markov chain Monte Carlo (MCMC) methods---including the Metropolis--Hastings algorithm and Gibbs sampling---construct a Markov chain whose stationary distribution is a target posterior $p(\bm{\theta}\mid\bm{x})$.  Detailed balance () is the key condition used to design the acceptance ratio.  Diffusion models (DDPM, score-based models) are also framed as Markov chains: the forward process adds Gaussian noise in discrete steps, and the learned reverse process denoises.

### Markov Decision Processes

The framework for sequential decision-making under uncertainty extends Markov chains by introducing actions and rewards.

> **Definition (Markov decision process (MDP))**
>
An MDP is a tuple $(\mathcal{S}, \mathcal{A}, P, R, \gamma)$ where:

- $\mathcal{S}$ is the state space,
  - $\mathcal{A}$ is the action space,
  - $P(s' \mid s, a) = \mathbb{P}(S_{t+1}=s' \mid S_t=s, A_t=a)$ is the transition kernel,
  - $R(s,a)$ is the expected reward: $R(s,a) = \mathbb{E}[R_t \mid S_t = s, A_t = a]$,
  - $\gamma \in [0,1]$ is the discount factor.

A *policy* $\pi(a\mid s)$ specifies the probability of taking action $a$ in state $s$.  Given a policy, the state sequence $S_0, S_1, \ldots$ is a Markov chain with transition probabilities

$$P^{\pi}(s'\mid s) = \sum_{a \in \mathcal{A}} \pi(a\mid s) P(s'\mid s,a).$$

> **Definition (Value functions)**
> The *state-value function* under policy $\pi$ is

$$
  V^{\pi}(s) = \mathbb{E}_{\pi}\biggl[\sum_{t=0}^{\infty}\gamma^t R_t  \bigg|  S_0 = s\biggr].$$

The *action-value function* is

$$
  Q^{\pi}(s,a) = \mathbb{E}_{\pi}\biggl[\sum_{t=0}^{\infty}\gamma^t R_t  \bigg|  S_0 = s, A_0 = a\biggr].$$

> **Theorem (Bellman expectation equation)**
>
For any policy $\pi$:

$$
  V^{\pi}(s) = \sum_{a}\pi(a\mid s)\biggl[R(s,a) + \gamma\sum_{s'}P(s'\mid s,a) V^{\pi}(s')\biggr].$$

> *Proof*
> Starting from the definition \eqref{eq:vf}:

$$V^{\pi}(s)
  = \mathbb{E}_{\pi}\Bigl[R_0 + \gamma\sum_{t=1}^{\infty}\gamma^{t-1}R_t  \Big|  S_0 = s\Bigr]
  = \sum_a \pi(a\mid s)\biggl[R(s,a) + \gamma\sum_{s'}P(s'\mid s,a) \mathbb{E}_{\pi}\Bigl[\sum_{t=0}^{\infty}\gamma^t R_t \Big| S_0 = s'\Bigr]\biggr],$$

where the second line uses the law of total expectation () and the Markov property.  The inner expectation is $V^{\pi}(s')$. ∎

> **Theorem (Bellman optimality equation)**
> The *optimal value function* $V^*(s) = \max_{\pi} V^{\pi}(s)$ satisfies:

$$
  V^*(s) = \max_{a \in \mathcal{A}}\biggl[R(s,a) + \gamma\sum_{s'}P(s'\mid s,a) V^*(s')\biggr].$$

An optimal policy $\pi^*$ exists and can be recovered as $\pi^*(s) = \operatorname{argmax}_a Q^*(s,a)$.

> **Relevance to AI: The Foundation of Reinforcement Learning**
> The Bellman equations are the starting point for virtually all RL algorithms.  Dynamic programming (value iteration, policy iteration) solves them exactly when the MDP is known.  When the MDP is unknown, temporal-difference (TD) learning, Q-learning, and actor--critic methods provide sample-based approximations.  The entire theory of AI agents acting sequentially in an environment rests on the MDP formalism and the probabilistic concepts developed in this chapter: conditional expectation, the Markov property, discounted sums, and policy-induced distributions.

### Filtering, Identification, and Realization Theory



### Backward Diffusion, Causality, and the Arrow of Time



## Monte Carlo Methods and Sampling

Many quantities of interest---posterior expectations, policy gradients, partition functions---are intractable to compute exactly.  Monte Carlo methods approximate them using random samples.

### Basic Monte Carlo Estimation

If we wish to estimate $\mu = \mathbb{E}_p[f(X)]$ and can draw i.i.d.\ samples $X^{(1)},\ldots,X^{(N)} \sim p$, then

$$\hat{\mu}_N = \frac{1}{N}\sum_{i=1}^{N} f(X^{(i)})$$

is an unbiased, consistent estimator with $\mathrm{Var}[\hat{\mu}_N] = \mathrm{Var}_p[f(X)]/N$.

### Importance Sampling

When sampling from $p$ is difficult but we can sample from a *proposal* distribution $q$, we use the identity

$$
  \mathbb{E}_p[f(X)] = \mathbb{E}_q\biggl[f(X) \frac{p(X)}{q(X)}\biggr].$$

The ratio $w(X) = p(X)/q(X)$ is the *importance weight*.

> **Proposition (Variance of importance sampling)**
>

$$\mathrm{Var}_q\biggl[f(X)\frac{p(X)}{q(X)}\biggr]
  = \mathbb{E}_p\biggl[f(X)^2\frac{p(X)}{q(X)}\biggr] - \mu^2.$$

The optimal proposal (minimizing variance) is $q^*(x) \propto |f(x)| p(x)$.

> **Relevance to AI: Off-Policy Learning**
> Importance sampling is the engine of off-policy reinforcement learning.  When an agent collects data using a behavior policy $\mu$ but wishes to evaluate or improve a target policy $\pi$, the importance sampling ratio $\prod_t \pi(a_t|s_t)/\mu(a_t|s_t)$ corrects for the distributional mismatch.  High variance of these ratios is a major practical challenge, addressed by techniques such as weighted importance sampling, truncation ($V$-trace), and retrace($\lambda$).

### The Reparameterization Trick

Suppose $X = g(\bm{\epsilon};\bm{\theta})$ where $\bm{\epsilon} \sim p(\bm{\epsilon})$ is a fixed noise distribution independent of $\bm{\theta}$.  Then

$$
  \nabla_{\bm{\theta}} \mathbb{E}_{p(x;\bm{\theta})}[f(X)]
  = \nabla_{\bm{\theta}} \mathbb{E}_{p(\bm{\epsilon})}\bigl[f\bigl(g(\bm{\epsilon};\bm{\theta})\bigr)\bigr]
  = \mathbb{E}_{p(\bm{\epsilon})}\bigl[\nabla_{\bm{\theta}} f\bigl(g(\bm{\epsilon};\bm{\theta})\bigr)\bigr].$$

The gradient can now be estimated by Monte Carlo without differentiating through the density, and typically has much lower variance than the score-function (REINFORCE) estimator.

> **Example**
> For $X \sim \mathcal{N}(\mu, \sigma^2)$, set $\epsilon \sim \mathcal{N}(0,1)$ and $g(\epsilon;\mu,\sigma) = \mu + \sigma\epsilon$.  Then $\nabla_\mu \mathbb{E}[f(X)] = \mathbb{E}[\nabla_\mu f(\mu + \sigma\epsilon)] = \mathbb{E}[f'(\mu + \sigma\epsilon)]$.

> **Relevance to AI: VAEs and Differentiable Sampling**
> The reparameterization trick is what makes training variational autoencoders (VAEs) practical: it allows backpropagation through the stochastic sampling step in the encoder.  It also appears in stochastic computation graphs and in continuous relaxations of discrete distributions (Gumbel-Softmax).

### The REINFORCE (Score Function) Estimator

When $f$ or the sampling distribution is not reparameterizable (e.g., for discrete random variables), we use the *log-derivative trick*:

$$
  \nabla_{\bm{\theta}} \mathbb{E}_{p(x;\bm{\theta})}[f(X)]
  = \mathbb{E}_{p(x;\bm{\theta})}\bigl[f(X) \nabla_{\bm{\theta}}\log p(X;\bm{\theta})\bigr].$$

> *Proof*
>

$$\nabla_{\bm{\theta}}\int f(x) p(x;\bm{\theta}) dx
  = \int f(x) \nabla_{\bm{\theta}} p(x;\bm{\theta}) dx
  = \int f(x) p(x;\bm{\theta}) \nabla_{\bm{\theta}}\log p(x;\bm{\theta}) dx. $$

 ∎

> **Relevance to AI: Policy Gradients**
> Equation~\eqref{eq:reinforce} is the mathematical core of the REINFORCE algorithm and all policy-gradient methods in RL.  With $f = R$ (return) and $p(x;\bm{\theta}) = \pi_{\bm{\theta}}(a|s)$, it gives $\nabla_{\bm{\theta}} \mathbb{E}[R] = \mathbb{E}[R \nabla_{\bm{\theta}}\log\pi_{\bm{\theta}}(a|s)]$.  The high variance of this estimator motivates the use of baselines, actor--critic architectures, and advantage functions.
