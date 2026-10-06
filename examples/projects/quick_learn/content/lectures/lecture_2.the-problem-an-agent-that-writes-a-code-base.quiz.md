# Prior

# Learned

1. Why does running the same prompt on a coding agent again give a different code base?
   - [ ] The agent forgets the prompt after its first file write
   - [x] Every step the agent takes, such as writing a file or running a command, is sampled
   - [ ] The test runner returns random results
   - [ ] The agent starts from a different repo each time
2. Evaluate these statements about the coding agent as a trajectory in the space of code bases:
   - [T] One wrong choice early in a run can derail the whole run
   - [F] Every trajectory that starts from an empty repo ends in the goal set
   - [T] The goal set is the set of acceptable code bases
3. The same prompt is run four times, and one run switches to Flask and deletes the tests. In the picture of the space of code bases, what is this run?
   - [ ] A trajectory that reaches the goal set by a shorter path
   - [x] A trajectory that ends outside the goal set of acceptable code bases
   - [ ] A trajectory that never leaves the empty repo
