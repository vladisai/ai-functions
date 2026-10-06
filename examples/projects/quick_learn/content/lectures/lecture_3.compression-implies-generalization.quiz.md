# Prior

1. What does it mean for a model to generalize?
   - [ ] It has zero training error
   - [ ] It uses as few parameters as possible
   - [ ] It was trained on a large dataset
   - [x] It performs well on new samples, not only on the training samples
2. Evaluate these statements:
   - [T] $N$ bits are enough to store $N$ binary labels.
   - [F] Storing a number to a lower precision takes more bits.

# Learned

1. By the Xu and Raginsky bound, when is the test loss guaranteed to be close to the training loss?
   - [ ] When the model has fewer parameters than there are samples
   - [x] When the information the weights store about the dataset, $I(W; D)$, is far smaller than the number of samples $N$
   - [ ] When the training error is zero
   - [ ] When the model stores every training label
2. Evaluate these statements:
   - [F] The bound is necessary: a model that stores many bits about its data cannot generalize.
   - [T] To compress the weights, what matters is how precisely they must be specified, not how many there are.
   - [T] A model with $N$ bits of weights can store all $N$ labels, reaching zero training error while learning nothing about new samples.
