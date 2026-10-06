# Prior

1. What is a linear classifier in the plane?
   - [ ] A curve that passes through every training sample
   - [ ] A lookup table of the training labels
   - [x] A line that assigns the points on one side to one class and the points on the other side to the other class
   - [ ] A rule that assigns every point to the most common class
2. Evaluate these statements:
   - [F] Halving the set of equally likely hypotheses halves the entropy.
   - [T] If $M$ equally likely hypotheses remain, their entropy is $\log M$.

# Learned

1. Why does more data leave a lower entropy $H(W \mid D)$?
   - [x] Each sample rules out some classifiers, so fewer classifiers remain compatible
   - [ ] More data makes the network larger
   - [ ] More data adds noise to the weights
   - [ ] More data makes the prior over classifiers uniform
2. Under a uniform prior over lines, a fraction $1/64$ of the lines remain consistent with the samples. How many bits do the samples give about the classifier?
   - [ ] 64 bits
   - [ ] 1/64 bit
   - [ ] 3 bits
   - [x] 6 bits
3. Evaluate these statements:
   - [T] Learning can be seen as cutting down the space of hypotheses.
   - [F] The information the samples give about the classifier goes down as more samples arrive.
