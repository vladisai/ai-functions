# Prior

1. Which factorization of the probability of a sequence $(h_1, \dots, h_T)$ is always correct?
   - [ ] $p(h_1, \dots, h_T) = \sum_t p(h_t)$
   - [x] $p(h_1, \dots, h_T) = \prod_t p(h_t \mid h_1, \dots, h_{t-1})$
   - [ ] $p(h_1, \dots, h_T) = \prod_t p(h_t)$
   - [ ] $p(h_1, \dots, h_T) = p(h_T \mid h_1)$
2. A distribution over three outcomes assigns them probabilities 0.6, 0.3 and 0.1. Evaluate these statements:
   - [T] A sample from it can be an outcome other than the most likely one
   - [F] Sampling from it always returns the outcome with probability 0.6

# Learned

1. When an LLM is viewed as a stochastic dynamical system, what is its state $x_t$?
   - [ ] The weights $w$ of the model
   - [x] The sequence of tokens in its history, $(h_1, \dots, h_t)$
   - [ ] Only the last token $h_t$
   - [ ] The distribution over the next token
2. Evaluate these statements:
   - [T] The transition function is the next-token distribution $p_w$ computed by the model
   - [F] Moving to the next state replaces the history with the sampled token
   - [T] The next state is $x_{t+1} = (h_1, \dots, h_t, h_{t+1})$
3. The history is “Fix failing test I 'll run”, and the next token is “the” with probability 0.6, “pytest” with 0.3 and “it” with 0.1. If “pytest” is sampled, what is the next state?
   - [x] “Fix failing test I 'll run pytest”
   - [ ] “pytest”
   - [ ] “Fix failing test I 'll run the”, since “the” is the most likely token
   - [ ] The distribution over “the”, “pytest” and “it”
