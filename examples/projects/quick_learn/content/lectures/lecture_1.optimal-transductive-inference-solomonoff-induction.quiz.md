# Prior

1. In Bayesian model averaging, how is a prediction formed?
   - [x] By averaging the predictions of all models, each weighted by its probability
   - [ ] By keeping only the model with the fewest parameters
   - [ ] By averaging only the models that fit the data worst
   - [ ] By picking one model uniformly at random
2. Evaluate these statements about Turing machines:
   - [T] A universal Turing machine can run any program given to it as input.
   - [T] There is no general procedure that decides whether an arbitrary program halts.
   - [F] Every program run on a Turing machine eventually halts.

# Learned

1. Which programs does Solomonoff's algorithm keep before predicting?
   - [x] Those that generate all the observed data bit by bit
   - [ ] Only the shortest program, discarding the others
   - [ ] Those that fit the training data, then checked separately on test data
   - [ ] Those that halt within a fixed time budget
2. Why is Solomonoff's algorithm better described as transductive than inductive?
   - [x] It uses all data ever observed, with no split between training and test data, and is optimal for data from any distribution
   - [ ] It assumes test data comes from the training distribution
   - [ ] It discards the data once the programs are selected
   - [ ] It needs a verifier for every prediction
3. Evaluate these statements:
   - [T] The universal prior gives more weight to shorter programs, in proportion to the negative exponential of their length.
   - [F] The algorithm is optimal only when test data comes from the same distribution as training data.
   - [T] The procedure could take forever, because some programs may not terminate.
