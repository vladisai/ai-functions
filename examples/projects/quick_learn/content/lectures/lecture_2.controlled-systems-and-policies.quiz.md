# Learned

1. Why does running the same prompt on a coding agent again give a different code base? [[lecture_2#The problem: an agent that writes a code base]]
   - [ ] The agent forgets the prompt after its first file write
   - [x] Every step the agent takes, such as writing a file or running a command, is sampled
   - [ ] The test runner returns random results
   - [ ] The agent starts from a different repo each time
2. Evaluate these statements about trajectories: [[lecture_2#The problem: an agent that writes a code base]] [[lecture_2#Stochastic dynamical systems]]
   - [T] A trajectory is the sequence of states $\tau = (x_0, x_1, \dots, x_T)$
   - [F] The transition function $p(\cdot \mid x_t)$ gives a single, fixed next state for each current state
   - [T] One wrong choice early in a run of a coding agent can derail the whole run
   - [F] Every trajectory that starts from an empty repo ends in the goal set of acceptable code bases
3. At $x_1$ the system moves ahead with probability 0.8 and to each side with 0.1. The action $u_1$ steers down-right. What happens to the transitions? [[lecture_2#Controlled systems and policies]]
   - [x] The probability 0.8 moves onto the down-right transition
   - [ ] The down-right transition gets probability 1 and the others 0
   - [ ] The probabilities stay the same, only the state changes
   - [ ] All three transitions get probability $1/3$
4. Evaluate these statements about policies: [[lecture_2#Controlled systems and policies]]
   - [T] A policy $\pi(\cdot \mid x_t)$ decides the next action based on the state, and the agent is the entity that enacts it
   - [T] An open-loop policy plans all actions ahead and executes them without looking at the result
   - [F] A closed-loop policy chooses its actions without looking at the observations
