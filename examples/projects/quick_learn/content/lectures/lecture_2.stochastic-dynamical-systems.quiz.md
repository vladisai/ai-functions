# Prior

1. At each step a car goes straight with probability 0.8, independently of the other steps. What is the probability that it goes straight two steps in a row?
   - [ ] 0.8
   - [x] 0.64
   - [ ] 0.16
   - [ ] 1.6
2. Evaluate these statements about a conditional distribution $p(y \mid x)$:
   - [T] For each fixed $x$, the probabilities $p(y \mid x)$ over all $y$ sum to 1
   - [F] $p(y \mid x)$ and $p(x \mid y)$ are always the same distribution

# Learned

1. In a stochastic dynamical system with $x_{t+1} \sim p(\cdot \mid x_t)$, what determines the distribution of the next state?
   - [x] The current state $x_t$
   - [ ] Nothing, the next state is chosen uniformly from $\mathcal{X}$
   - [ ] Only the time $t$
   - [ ] The goal set
2. Evaluate these statements:
   - [T] A trajectory is the sequence of states $\tau = (x_0, x_1, \dots, x_T)$
   - [F] The transition function gives a single, fixed next state for each current state
   - [F] Two runs of the system from the same $x_0$ always produce the same trajectory
3. Why does the car on ice drift off course when the driver does not correct it?
   - [ ] The intended move points away from the goal
   - [x] Random slips to the cell above or below accumulate over the steps
   - [ ] The transition function changes over time
   - [ ] The car slips with probability 0.8 at every step
