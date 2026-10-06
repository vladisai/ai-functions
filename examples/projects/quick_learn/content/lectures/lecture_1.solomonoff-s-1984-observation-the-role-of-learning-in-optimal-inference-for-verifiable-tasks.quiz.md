# Prior

1. In Levin's search, what does the constant slowdown factor depend on?
   - [x] It grows exponentially with the length of the shortest optimal program for the task
   - [ ] The size of the input instance
   - [ ] The number of training samples
   - [ ] Nothing, it is the same for all tasks
2. Evaluate these statements about statistical learning:
   - [T] Generalization means that a function that worked on past data also works on future data from the same distribution.
   - [F] The generalization bound rewards storing as much information about the training set in the weights as possible.

# Learned

1. According to Solomonoff's 1984 observation, what is the only role learning can play in optimal inference for verifiable tasks?
   - [x] Reducing the constant in Levin's search, so new tasks are solved faster
   - [ ] Reducing uncertainty about the test distribution
   - [ ] Shrinking the set of hypotheses
   - [ ] Removing the need for a verifier
2. Evaluate these statements:
   - [T] Having solved many tasks before lets one sample or compose past solutions into a solution to a new, unforeseen task.
   - [F] Like statistical learning, this view of learning advocates shedding information about past data.
   - [T] Reusing past solutions can reduce the time to solve new tasks exponentially.
