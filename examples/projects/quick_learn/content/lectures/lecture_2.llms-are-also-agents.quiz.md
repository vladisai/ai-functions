# Prior

1. In a controlled system $x_{t+1} \sim p(\cdot \mid x_t, u_t)$, what is an agent?
   - [ ] The transition function $p$
   - [x] The entity that enacts a policy choosing actions $u_t$ from the state
   - [ ] The state space $\mathcal{X}$
2. Evaluate these statements:
   - [T] An action $u_t$ changes the likelihood of each next state
   - [T] A human controls an LLM by adding messages to its state

# Learned

1. When the LLM acts as an agent on its environment, what are its actions?
   - [ ] The messages it receives from the human
   - [x] Tool calls, such as editing a file, running the tests or searching the web
   - [ ] Updates to its own weights
   - [ ] The next-token probabilities it computes
2. What does partial observability mean for an agent acting on the world?
   - [ ] The agent can take only some of the possible actions
   - [ ] The world is deterministic, but the agent is not
   - [x] The agent does not know the full state of the world and has to act based only on the observations $o_{t+1} = g(\mathrm{world}_{t+1})$
   - [ ] The human sees only part of the agent's messages
3. Evaluate these statements:
   - [T] The world is a second source of stochasticity
   - [T] The world is a second source of information
   - [F] An action $a_t$ changes the world deterministically
