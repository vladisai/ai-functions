# Prior

1. Under the optimal code for a distribution $p$, how many bits does a sample $x$ take?
   - [ ] $p(x)$
   - [ ] Exactly $H(X)$, for every sample
   - [ ] $\log N$, for every sample
   - [x] $-\log p(x)$
2. Evaluate these statements:
   - [T] Minimizing the negative log-likelihood of the data is the same as maximizing the probability the model gives to the data.
   - [F] A model that gives the data a higher probability has a higher negative log-likelihood.

# Learned

1. What is the minimum of the cross-entropy loss, and when is it reached?
   - [ ] 0, reached when $p_w$ puts all its mass on the most frequent sample
   - [x] $H(X)$, reached exactly when $p_w(x) = p(x)$
   - [ ] $H(X)$, reached for any $p_w$ that gives every sample a positive probability
   - [ ] $\log N$, reached when $p_w$ is uniform
2. Evaluate these statements:
   - [T] The cross-entropy loss is the loss used to train LLMs.
   - [T] Learning the data distribution is equivalent to learning the best compression of the data.
   - [F] Minimizing the cross-entropy loss requires knowing the true distribution $p(x)$, not just samples from it.
