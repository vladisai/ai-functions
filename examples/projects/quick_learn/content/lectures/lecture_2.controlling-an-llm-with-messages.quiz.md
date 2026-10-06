# Learned

1. The history is “Fix failing test I 'll run”, and the next token is “the” with probability 0.6, “pytest” with 0.3 and “it” with 0.1. If “pytest” is sampled, what is the next state? [[lecture_2#LLMs as stochastic dynamical systems]]
   - [x] “Fix failing test I 'll run pytest”
   - [ ] “pytest”
   - [ ] “Fix failing test I 'll run the”, since “the” is the most likely token
   - [ ] The distribution over “the”, “pytest” and “it”
2. Where does the stochasticity enter the loop of generating a token? [[lecture_2#Inside the state: the KV cache]]
   - [ ] When the keys and values are written into the cache
   - [ ] In the forward pass, which outputs a random token
   - [x] When a token is sampled from the distribution that the forward pass outputs
   - [ ] When the query attends over the cached keys
3. Evaluate these statements: [[lecture_2#LLMs as stochastic dynamical systems]] [[lecture_2#Inside the state: the KV cache]] [[lecture_2#Controlling an LLM with messages]]
   - [T] The transition function of the LLM is the next-token distribution $p_w$ that the model computes
   - [F] Tokens injected by the controller, such as a tool output, are sampled from $p_w$
   - [T] Once the context window is full, the state can no longer grow
   - [F] A human message $u_t$ controls the LLM by changing its weights $w$
4. Why is closed-loop control of a coding agent more robust than open-loop control, and what does it cost? [[lecture_2#Controlling an LLM with messages]]
   - [ ] The initial prompt is longer and anticipates everything, at the cost of more tokens on every step
   - [x] The human reads what the agent did and corrects it with new messages, at the cost of human attention at every step
   - [ ] The agent samples with less randomness after each message, at the cost of slower generation
   - [ ] The human retrains the model after each step, at the cost of compute and time
