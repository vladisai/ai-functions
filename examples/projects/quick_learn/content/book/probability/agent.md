## About this material

This is a Probability and Statistics Primer for an AI/ML textbook. It covers foundational probability through advanced topics needed for understanding modern AI agents.

## Pre-conditions

What the reader needs to know *before* engaging with this chapter. If they lack these, direct them to prerequisite resources before proceeding.

- **Multivariate calculus**: partial derivatives, gradients, multivariable integration, change of variables. At the level of an introductory college course or advanced placement high school course.
- **Linear algebra**: vectors, matrices, matrix multiplication, eigenvalues, positive definiteness. Same level as above.
- **Basic probability** (helpful but not strictly required): combinatorics, standard distributions, elementary conditional probability. Readers without this will need the full core material rather than the expert summary.

If a reader's quiz answers or chat questions suggest they're missing pre-conditions (e.g. struggling with basic derivatives or matrix operations), recommend they review:
- Bertsekas & Tsitsiklis, *Introduction to Probability* (2008)
- Blitzstein & Hwang, *Introduction to Probability* (2019)

## Post-conditions

What the reader should understand *after* completing this chapter. The diagnostic quizes test these. Use quiz results to determine which post-conditions are met and which need reinforcement.

- **Random variables and distributions**: define random variables, PMFs, PDFs; work with standard distributions (Bernoulli, Categorical, Gaussian, Poisson, Uniform); compute probabilities from densities.
- **Expectation and moments**: compute expectations, variances, covariances; apply linearity of expectation; use moment-generating functions.
- **Key inequalities**: state and apply Markov's, Chebyshev's, and Jensen's inequality; know when each is useful.
- **Law of large numbers and CLT**: distinguish LLN from CLT; know their assumptions and conclusions.
- **Conditioning and independence**: apply Bayes' theorem; use the law of total expectation and total variance; distinguish conditional independence from unconditional independence.
- **Bayesian reasoning**: understand exchangeability and de Finetti's theorem; relate prior, likelihood, and posterior; distinguish MAP from MLE.
- **Information-theoretic quantities**: define and compute entropy, KL divergence, mutual information, Fisher information; know their key properties (e.g. KL is non-negative, not symmetric).
- **Markov chains and MDPs**: define Markov property; compute stationary distributions; write Bellman equations; understand policies and value functions.
- **Monte Carlo methods**: explain importance sampling and when it helps; derive the REINFORCE estimator; explain the reparameterization trick and when it applies vs. REINFORCE.
- **Estimation**: define MLE and MAP; understand bias-variance tradeoff; know that MLE is consistent but not always unbiased; relate Fisher information to estimator variance (Cramer-Rao).



## Topic dependencies

- Expectation depends on random variables and distributions.
- Inequalities (Markov, Chebyshev, Jensen) depend on expectation.
- KL divergence depends on expectation and log-probabilities.
- Markov chains depend on conditional probability.
- MDPs depend on Markov chains and expectation.
- Importance sampling depends on expectation and distributions.
- REINFORCE depends on importance sampling and gradients.
- Reparameterization trick depends on distributions and gradients.
- Fisher information depends on KL divergence and expectation.
- MAP estimation depends on Bayes' theorem and optimization.

## Common misconceptions

- Confusing PDF values with probabilities (PDF can exceed 1).
- Thinking KL divergence is symmetric.
- Believing conditional independence implies unconditional independence (or vice versa).
- Confusing the law of large numbers with the central limit theorem.
- Thinking MLE is always unbiased.
- Conflating the Bellman equation with the Bellman optimality equation.

## Style

By default the chapter targets someone already comfortable with the material: concise prose with key definitions and formulas woven into short explanatory paragraphs. It is not a cheat sheet and not a textbook either. Each concept gets a sentence or two of context, then the math. The learned quizzes are empty until the reader shows gaps. When adapting to the reader's background or quiz results, expand the sections where they showed gaps with worked examples, intuition and longer explanations as needed, and use the learned quiz to test the material.
