# Prior

1. What is the obstacle to running Solomonoff's procedure?
   - [x] It could take forever, since some programs may not terminate
   - [ ] It is optimal only for data from the training distribution
   - [ ] It ignores the length of the programs
   - [ ] It needs labeled data
2. Evaluate these statements:
   - [T] An algorithm at most a constant factor $c$ slower than another can still be far slower in practice if $c$ is huge.
   - [F] Running many programs by interleaving their steps (dovetailing) requires each program to finish before the next one starts.

# Learned

1. Levin's search takes no worse than a constant factor longer than the optimal bespoke algorithm for a task. What is the catch?
   - [x] The constant is the exponential of the length of the shortest optimal bespoke algorithm, which can be astronomical
   - [ ] It only works on NP-complete problems
   - [ ] The constant grows with the size of each instance
   - [ ] It requires data from a known distribution
2. Evaluate these statements:
   - [T] The constant in Levin's search depends on the task, but not on the particular instance.
   - [T] "Universally fast" means that no other algorithm does better across all possible programs.
   - [F] Levin search has had a large impact on practical machine learning.
