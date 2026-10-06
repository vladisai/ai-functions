# Prior

1. $X \to Y \to Z$ is a Markov chain, so $Z$ is computed from $Y$ alone. What does the data processing inequality say?
   - [x] $I(X; Z) \le I(X; Y)$
   - [ ] $I(X; Z) \ge I(X; Y)$
   - [ ] $I(X; Z) = I(X; Y)$
   - [ ] $I(X; Z) = 0$
2. Evaluate these statements about the mutual information $I(X; Y)$:
   - [T] $I(X; Y) = 0$ when $X$ and $Y$ are independent
   - [F] $I(X; Y)$ can be negative

# Learned

1. Where does the model get information about the intent of the task?
   - [ ] From the prior in its weights
   - [ ] From tool outputs
   - [x] From the human's messages, since the intent exists only in the human's head
   - [ ] From thinking about the task
2. Evaluate these statements:
   - [F] A sampled thought $h_{t+1} \sim p_w(\cdot \mid x_t)$ adds information about the task that was not in $x_t$
   - [T] Thinking can make information usable for a bounded model
   - [T] The policy can act only on what the model has in its state
3. Through which channels does information about the world, such as the code, the docs and the tests, enter?
   - [ ] Only through user messages
   - [x] Through tool outputs and through the prior in the weights
   - [ ] Only through the model's own thoughts
   - [ ] It does not enter, the model must guess it
