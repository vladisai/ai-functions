# Prior

1. What makes an inference transductive?
   - [x] The loss is available during inference, so candidate outcomes can be evaluated
   - [ ] The inference function is trained on a large dataset
   - [ ] Training and test data come from the same distribution
   - [ ] The decision is binary
2. Evaluate these statements:
   - [T] The elements of a countable set can be listed one after another, like the integers.
   - [F] Every countable set is finite.

# Learned

1. In transductive inference, what is the only question left?
   - [x] How much time it takes to find a decision or action that optimizes the loss
   - [ ] How uncertain the outcome of the decision is
   - [ ] Whether the test datum comes from the training distribution
   - [ ] How to choose the inductive bias
2. Evaluate these statements:
   - [T] Transductive inference involves no uncertainty, because the quality of inference can be monitored along the way.
   - [T] Since the set of possible decisions is usually countable or finite, one can fall back on brute-force search in the worst case.
   - [F] In transductive inference the inference function is fixed in advance and does not depend on the test datum.
