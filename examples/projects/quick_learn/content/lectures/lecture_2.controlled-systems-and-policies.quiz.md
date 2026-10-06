# Prior

1. What does $p(a \mid b, c)$ denote?
   - [x] The distribution of $a$ given both $b$ and $c$
   - [ ] The joint distribution of $a$, $b$ and $c$
   - [ ] The distribution of $b$ and $c$ given $a$
   - [ ] The product $p(a)\,p(b)\,p(c)$
2. Evaluate these statements about a stochastic dynamical system $x_{t+1} \sim p(\cdot \mid x_t)$:
   - [T] The next state is drawn from a distribution that depends on the current state
   - [F] A trajectory is a single state of the system

# Learned

1. What does an action $u_t$ do in a controlled system $x_{t+1} \sim p(\cdot \mid x_t, u_t)$?
   - [ ] It sets the next state with certainty
   - [x] It changes the likelihood of transitioning to each next state
   - [ ] It changes the state space $\mathcal{X}$
   - [ ] It removes the randomness from the system
2. Evaluate these statements about policies:
   - [T] A policy $\pi(\cdot \mid x_t)$ decides the next action based on the state
   - [T] An open-loop policy plans all actions ahead and executes them without looking at the result
   - [F] The policy is the entity that enacts the agent
3. At $x_1$ the system moves ahead with probability 0.8 and to each side with 0.1. The action $u_1$ steers down-right. What happens to the transitions?
   - [x] The probability 0.8 moves onto the down-right transition
   - [ ] The down-right transition gets probability 1 and the others 0
   - [ ] The probabilities stay the same, only the state changes
   - [ ] All three transitions get probability $1/3$
