# Prior

1. At each step a car goes straight with probability 0.8, independently of the other steps. What is the probability that it goes straight two steps in a row? [[lecture_2#Stochastic dynamical systems]]
   - [ ] 0.8
   - [x] 0.64
   - [ ] 0.16
   - [ ] 1.6
2. Evaluate these statements about conditional distributions and sampling: [[lecture_2#Stochastic dynamical systems]] [[lecture_2#Controlled systems and policies]] [[lecture_2#LLMs as stochastic dynamical systems]]
   - [T] For each fixed $x$, the probabilities $p(y \mid x)$ over all $y$ sum to 1
   - [T] $p(a \mid b, c)$ is the distribution of $a$ given both $b$ and $c$
   - [F] $p(y \mid x)$ and $p(x \mid y)$ are always the same distribution
   - [F] Sampling from a distribution with probabilities 0.6, 0.3 and 0.1 always returns the outcome with probability 0.6
3. Which factorization of the probability of a sequence $(h_1, \dots, h_T)$ is always correct? [[lecture_2#LLMs as stochastic dynamical systems]]
   - [ ] $p(h_1, \dots, h_T) = \sum_t p(h_t)$
   - [x] $p(h_1, \dots, h_T) = \prod_t p(h_t \mid h_1, \dots, h_{t-1})$
   - [ ] $p(h_1, \dots, h_T) = \prod_t p(h_t)$
   - [ ] $p(h_1, \dots, h_T) = p(h_T \mid h_1)$
4. Evaluate these statements about attention in a decoder-only (causal) transformer: [[lecture_2#Inside the state: the KV cache]]
   - [T] The output for a token averages the values of the tokens, weighted by how well its query matches their keys
   - [T] A token can attend to itself and to the tokens before it
   - [F] A token can attend to tokens that come after it
5. $\tau$ is a random trajectory. What is $\mathbb{E}_\tau[f(\tau)]$? [[lecture_2#Rewards and costs]]
   - [ ] The value of $f$ on the most likely trajectory
   - [x] The average of $f(\tau)$ over trajectories, weighted by their probabilities
   - [ ] The largest value of $f(\tau)$ over all trajectories
   - [ ] The probability that $f(\tau) > 0$
6. $X \to Y \to Z$ is a Markov chain, so $Z$ depends on $X$ only through $Y$. What does the data processing inequality say? [[lecture_2#Information]]
   - [x] $I(X; Z) \le I(X; Y)$
   - [ ] $I(X; Z) \ge I(X; Y)$
   - [ ] $I(X; Z) = I(X; Y)$
   - [ ] $I(X; Z) = 0$
