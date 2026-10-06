# Prior

1. In stochastic gradient descent, why is the gradient noisy?
   - [ ] The weights are initialized at random
   - [ ] The loss function changes at random
   - [ ] Floating-point rounding errors accumulate
   - [x] Each step computes it on a random minibatch, not on the whole dataset
2. Evaluate these statements:
   - [T] The learning rate scales the size of each update step.
   - [T] The batch size is the number of samples used to compute each gradient.
   - [F] A larger batch makes the minibatch gradient noisier.

# Learned

1. Why do the weights at a flat minimum need fewer bits than at a sharp minimum?
   - [ ] A flat minimum has a lower training loss
   - [ ] A flat minimum uses fewer parameters
   - [x] The noise does not kick $w$ out of a flat minimum, so a rough $w$ is enough
   - [ ] SGD never reaches sharp minima
2. Which change keeps the scale of the SGD noise about the same?
   - [x] Doubling both the learning rate and the batch size
   - [ ] Doubling only the learning rate
   - [ ] Doubling only the batch size
   - [ ] Halving the learning rate and doubling the batch size
3. Evaluate these statements:
   - [T] The weights can only keep the details that survive the SGD noise.
   - [T] Less noise, as with a large batch, leads to sharper minima and worse generalization.
