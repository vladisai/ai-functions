# Learned

1. The LLM samples a tool call $a_t$, such as `run_tests()`. Who executes it, and what is the LLM's new state? [[lecture_2#How LLMs act: tool calling]]
   - [ ] The LLM executes it inside its forward pass, and the new state is $x_{t+1} = o_t$
   - [x] The harness executes it and adds the call and the tool result to the state, $x_{t+1} = (x_t, a_t, o_t)$
   - [ ] The harness executes it and appends the full state of the world, $x_{t+1} = (x_t, \mathrm{world}_{t+1})$
   - [ ] The human executes it, and the state stays $x_t$
2. What does partial observability mean for an LLM agent acting on the world? [[lecture_2#LLMs are also agents]]
   - [ ] The agent can take only some of the possible actions
   - [ ] The world is deterministic, but the agent's policy is not
   - [x] The agent does not see the full state of the world and has to act based only on its observations
   - [ ] The human sees only part of the agent's messages
3. Evaluate these statements about rewards and costs: [[lecture_2#Rewards and costs]]
   - [T] The goal of control is a policy $\pi$ that maximizes $\mathbb{E}_\tau \left[ R(x_T) - \sum_t c(x_t, u_t) \right]$
   - [F] Rewards for an LLM agent usually score each sampled token rather than the final state
   - [T] Every closed-loop message adds to the cost of human effort
   - [F] A KV or prompt cache processes fewer tokens because it stops the state from growing
4. Evaluate these statements about information: [[lecture_2#Information]]
   - [F] A sampled thought $h_{t+1} \sim p_w(\cdot \mid x_t)$ adds information about the task that was not in $x_t$
   - [T] Thinking can make information usable for a bounded model
   - [T] Information about the intent of the task exists only in the human's head, so the model has to acquire it through messages
   - [F] Information about the world, such as the code and the tests, enters only through the human's messages
