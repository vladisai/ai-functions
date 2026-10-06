# Learned

1. In the information bottleneck $L = H(T \mid Z) + \beta I(Z; X)$, what happens to the best $Z$ as $\beta$ grows? [[lecture_3#The information bottleneck]]
   - [ ] $Z$ keeps more information about the input, so the uncertainty about the task drops
   - [x] $Z$ keeps less information about the input, even at the price of more uncertainty about the task
   - [ ] $Z$ keeps all the information about the input, whatever the task
   - [ ] Nothing changes, since $\beta$ only rescales the loss
2. Under a uniform prior over lines, a fraction $1/64$ of the lines remain consistent with the samples. How many bits do the samples give about the classifier? [[lecture_3#Inductive learning and information]]
   - [ ] 64 bits
   - [x] 6 bits
   - [ ] 1/64 bit
   - [ ] 3 bits
3. By the Xu and Raginsky bound, when is the test loss guaranteed to be close to the training loss? [[lecture_3#Compression implies generalization]]
   - [ ] When the model has fewer parameters than there are samples
   - [ ] When the training error is zero
   - [ ] When the model stores every training label
   - [x] When the information the weights store about the dataset, $I(W; D)$, is far smaller than the number of samples $N$
4. Evaluate these statements: [[lecture_3#Compression implies generalization]] [[lecture_3#SGD noise limits information]] [[lecture_3#Deep networks can memorize]]
   - [T] To compress the weights, what matters is how precisely they must be specified, not how many there are.
   - [T] The weights at a flat minimum need fewer bits than at a sharp minimum, since the SGD noise does not kick $w$ out and a rough $w$ is enough.
   - [F] Less SGD noise, as with a large batch, leads to flatter minima and better generalization.
   - [F] A network that can fit random labels perfectly cannot generalize on real labels.
