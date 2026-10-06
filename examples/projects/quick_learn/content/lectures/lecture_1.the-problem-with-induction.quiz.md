# Prior

1. Evaluate these statements about uniform generalization bounds:
   - [T] They hold for any distribution $P$, provided the training data and the future data come from that same $P$.
   - [F] The training loss in the bound is computed on future data.
2. What is a held-out dataset used for?
   - [x] To estimate performance on data that was not used for training
   - [ ] To enlarge the training set
   - [ ] To compute the regularizer
   - [ ] To choose the loss function

# Learned

1. Why is the assumption that future data comes from the same distribution as past data at best unverifiable?
   - [x] Future data is not instantiated yet, so it cannot be checked
   - [ ] Training sets are always too small
   - [ ] Held-out sets always come from a different distribution
   - [ ] Distributions cannot be described mathematically
2. Evaluate these statements:
   - [T] A finite dataset $D$ could have been drawn, with the same likelihood, from infinitely many distributions.
   - [F] Stationarity is a sound assumption for real data in finance, climate or language, as it is for dice.
   - [T] In the lecture's view, fixes for out-of-distribution behavior or covariate shift solve problems created by assuming a distribution in the first place.
3. In the lecture's reading of Hume, what would a rational justification of induction imply?
   - [x] That nature is stationary: unseen instances resemble seen ones and nature's course stays the same
   - [ ] That the training set is large enough
   - [ ] That the loss function is known during inference
   - [ ] That the set of hypotheses is finite
