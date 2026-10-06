# Prior

1. An agent takes an action $a_t$ on its environment. What does the action produce?
   - [x] A new world state $\mathrm{world}_{t+1}$ and an observation $o_{t+1} = g(\mathrm{world}_{t+1})$
   - [ ] Only a new message from the human
   - [ ] A full copy of the world state for the agent
2. Evaluate these statements:
   - [T] The LLM's state is its token history, and new tokens are appended to it
   - [F] Under partial observability, the agent sees the full state of the world

# Learned

1. Who executes the tool call that the LLM samples, such as `web_search`?
   - [ ] The LLM, inside its forward pass
   - [x] The harness
   - [ ] The human
   - [ ] Nobody, the call is only written into the state
2. After a tool call, what is the LLM's new state?
   - [ ] $x_{t+1} = o_t$
   - [ ] $x_{t+1} = (x_t, \mathrm{world}_{t+1})$
   - [x] $x_{t+1} = (x_t, a_t, o_t)$
   - [ ] $x_{t+1} = x_t$, since tools do not change the state
3. Evaluate these statements:
   - [T] The tool call action is sampled from the model, $a_t \sim p_w(\cdot \mid x_t)$
   - [T] The tool result is the observation $o_t$, which the harness adds to the LLM's state
   - [F] The full state of the world is appended to the LLM's state after each tool call
