# Prior

1. By the information-theoretic bound, what does storing few bits about the data in the weights, compared with the number of samples, guarantee?
   - [ ] The training error is zero
   - [x] The test error is close to the training error
   - [ ] The model can fit any labels
   - [ ] The model has few parameters
2. Evaluate these statements:
   - [T] Random labels have no relation to the inputs, so a model that fits them has nothing to carry over to new samples.
   - [T] With $N$ labeled samples, $N$ bits of weights are enough to store every label.

# Learned

1. Why is it a problem for the compression story that a network can fit random labels perfectly?
   - [ ] It shows that the network cannot generalize on real labels
   - [ ] It shows that SGD noise is too large to learn anything
   - [x] It shows that the network has room to store everything, yet on real labels it generalizes anyway
   - [ ] It shows that random labels carry more useful information than real labels
2. Evaluate these statements:
   - [T] Why deep networks generalize even though they can memorize is mostly an open problem.
   - [T] One candidate explanation is that SGD finds flat minima, which are robust to noise in the weights and so cheap to describe.
   - [F] The capacity of a network determines what it actually stores.
