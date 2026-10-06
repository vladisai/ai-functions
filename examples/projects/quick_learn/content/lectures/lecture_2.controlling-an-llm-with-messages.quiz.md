# Prior

1. When an LLM is viewed as a stochastic dynamical system, what is its state?
   - [ ] Its weights
   - [x] The sequence of tokens in its history
   - [ ] The last token it sampled
2. Evaluate these statements about policies:
   - [T] A closed-loop policy chooses each action based on observations
   - [F] An open-loop policy looks at the result of each action before choosing the next one

# Learned

1. How does a human message $u_t$ change the state of the LLM?
   - [ ] It replaces the state with the message
   - [x] It is appended to the state, $x_{t+1} = (x_t, u_t)$
   - [ ] It changes the model's weights
   - [ ] It changes the transition function $p_w$
2. Evaluate these statements:
   - [T] In open-loop control, the single initial prompt has to anticipate everything
   - [T] Closed-loop control is more robust, but it costs human attention at every step
   - [F] In closed-loop control, the human writes all the messages before the agent starts
3. In the open-loop example the agent switches to Flask and declares itself done. What keeps the agent on FastAPI in the closed-loop example?
   - [ ] A longer initial prompt
   - [x] The human reads what the agent did and sends a message that corrects it
   - [ ] The agent samples with less randomness
   - [ ] The tests reject Flask code
