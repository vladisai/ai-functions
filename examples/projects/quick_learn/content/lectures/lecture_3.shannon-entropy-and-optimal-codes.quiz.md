# Prior

1. What is $-\log_2 (1/8)$?
   - [ ] -3
   - [ ] 1/8
   - [ ] 8
   - [x] 3
2. Evaluate these statements:
   - [F] A value with a smaller probability has a smaller $-\log p$.
   - [T] The probabilities of all the values of a discrete random variable sum to 1.
   - [T] For $0 < p < 1$, $-\log p$ is positive.

# Learned

1. Under an optimal code, how long is the codeword of a symbol with probability 1/4?
   - [ ] 4 bits
   - [x] 2 bits
   - [ ] 1/4 bit
   - [ ] 1 bit
2. Evaluate these statements:
   - [T] No lossless code can use fewer than $H(X)$ bits per symbol on average.
   - [F] An optimal code gives every symbol a codeword of the same length.
   - [T] The negative log-likelihood $-\log p(x)$ of a sample is the length of its optimal code.
3. Why does the optimal code for "ha ha ha ha, very very funny joke" take 14 bits, while a fixed-length code takes 16?
   - [ ] The optimal code drops the repeated words
   - [x] Frequent words get shorter codewords, so the average length drops to the entropy of 1.75 bits per word
   - [ ] The optimal code encodes letters instead of words
   - [ ] A fixed-length code needs 3 bits per word for four distinct words
