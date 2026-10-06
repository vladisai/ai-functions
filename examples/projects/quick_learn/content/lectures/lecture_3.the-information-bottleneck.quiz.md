# Prior

1. What does $H(T \mid Z)$ measure?
   - [ ] The information that $Z$ has about $T$
   - [ ] The uncertainty that remains about $Z$ once $T$ is known
   - [ ] The total uncertainty of $T$ and $Z$ together
   - [x] The uncertainty that remains about $T$ once $Z$ is known
2. Evaluate these statements about minimizing a loss $A + \beta B$ with $\beta > 0$:
   - [T] A larger $\beta$ penalizes $B$ more heavily.
   - [F] The minimum always has $A = 0$.

# Learned

1. What kind of representation $Z$ does minimizing $L = H(T \mid Z) + \beta I(Z; X)$ ask for?
   - [ ] One that keeps all the information about the input
   - [ ] One that keeps as little information as possible, whatever the task
   - [x] One that reduces the uncertainty about the task while keeping as little information about the input as possible
   - [ ] One that keeps the uncertainty about the task as large as possible
2. Evaluate these statements:
   - [T] When training, the term $\beta I(W; D)$ penalizes the information the weights store about the dataset.
   - [F] A larger $\beta$ pushes $Z$ to keep more information about the input $X$.
   - [T] Given a task, the semantic information is the information needed for the task.
