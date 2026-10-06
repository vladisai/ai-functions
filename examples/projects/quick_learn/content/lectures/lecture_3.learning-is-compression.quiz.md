# Learned

1. An object is one of $N = 32$ equally likely objects, and we learn that it is in the left half of them. What is its entropy before and after? [[lecture_3#Entropy measures the volume of uncertainty]] [[lecture_3#Entropy of a uniform distribution]]
   - [ ] 32 bits before, and 16 bits after
   - [ ] 5 bits before, and 2.5 bits after
   - [x] 5 bits before, and 4 bits after
   - [ ] 32 bits before, and 31 bits after
2. Why does the optimal code for "ha ha ha ha, very very funny joke" take 14 bits, while a fixed-length code takes 16? [[lecture_3#Shannon entropy and optimal codes]]
   - [ ] The optimal code drops the repeated words
   - [x] Frequent words get shorter codewords, so the average length drops to the entropy of 1.75 bits per word
   - [ ] The optimal code gives every word a codeword of 1.75 bits
   - [ ] The optimal code encodes letters instead of words
3. What is the minimum of the cross-entropy loss, and when is it reached? [[lecture_3#Learning is compression]]
   - [ ] 0, reached when $p_w$ puts all its mass on the most frequent sample
   - [ ] $H(X)$, reached for any $p_w$ that gives every sample a positive probability
   - [x] $H(X)$, reached exactly when $p_w(x) = p(x)$
   - [ ] $\log N$, reached when $p_w$ is uniform
4. Evaluate these statements: [[lecture_3#What information to keep?]] [[lecture_3#Shannon entropy and optimal codes]] [[lecture_3#Learning is compression]]
   - [T] A coding agent that reads a 500k-token log with an 8k-token context, like a network that trains on 150 TB of data into 0.5 TB of weights, cannot keep everything and must choose what to keep.
   - [F] A clever enough lossless code can use fewer than $H(X)$ bits per symbol on average.
   - [T] The negative log-likelihood $-\log p(x)$ of a sample is the length of its optimal code.
   - [F] Minimizing the cross-entropy loss requires knowing the true distribution $p(x)$, not just samples from it.
