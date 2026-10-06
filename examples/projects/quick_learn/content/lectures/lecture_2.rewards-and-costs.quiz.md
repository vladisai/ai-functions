# Prior

1. $\tau$ is a random trajectory. What is $\mathbb{E}_\tau[f(\tau)]$?
   - [ ] The value of $f$ on the most likely trajectory
   - [x] The average of $f(\tau)$ over trajectories, weighted by their probabilities
   - [ ] The largest value of $f(\tau)$ over all trajectories
2. Evaluate these statements:
   - [T] $\mathbb{E}[A - B] = \mathbb{E}[A] - \mathbb{E}[B]$ for any random variables $A$ and $B$
   - [F] A policy with the highest expected reward gets a high reward on every trajectory

# Learned

1. What is the goal of control in this section?
   - [ ] To minimize the number of actions, whatever the reward
   - [ ] To maximize the reward of the most likely trajectory
   - [x] To find a policy $\pi$ that maximizes $\mathbb{E}_\tau \left[ R(x_T) - \sum_t c(x_t, u_t) \right]$
   - [ ] To maximize the reward of each action separately
2. Evaluate these statements about rewards and costs for LLM agents:
   - [T] Every closed-loop message adds to the cost of human effort
   - [T] The cost of computation is usually ignored in control theory, but it is fundamental for AI agents
   - [F] Rewards for an LLM agent usually score each sampled token rather than the final state
3. Why does a KV or prompt cache cut the tokens processed over many agent turns so much?
   - [ ] It shortens the prompt
   - [x] It processes only the new tokens each turn, instead of re-reading the whole growing state
   - [ ] It stops the state from growing
   - [ ] It skips the tool calls
