# Prior

1. Evaluate these statements about base-2 logarithms and binary numbers: [[lecture_3#Entropy measures the volume of uncertainty]] [[lecture_3#Entropy of a uniform distribution]] [[lecture_3#Shannon entropy and optimal codes]]
   - [T] $\log_2 16 = 4$
   - [T] $-\log_2 (1/8) = 3$
   - [F] $\log_2 (v/2) = (\log_2 v)/2$
   - [T] With 3 binary digits one can write $2^3 = 8$ different numbers.
2. Which identity for the probability of three tokens holds in general? [[lecture_3#Measuring information with an LLM]]
   - [ ] $p(x_1, x_2, x_3) = p(x_1) + p(x_2 \mid x_1) + p(x_3 \mid x_1, x_2)$
   - [ ] $p(x_1, x_2, x_3) = p(x_1)\,p(x_2)\,p(x_3)$
   - [x] $p(x_1, x_2, x_3) = p(x_1)\,p(x_2 \mid x_1)\,p(x_3 \mid x_1, x_2)$
   - [ ] $p(x_1, x_2, x_3) = p(x_3 \mid x_1, x_2)$
3. Evaluate these statements about conditioning: [[lecture_3#Entropy measures the volume of uncertainty]] [[lecture_3#Mutual information]] [[lecture_3#Measuring information with an LLM]]
   - [F] If an object is equally likely to be anywhere in a region, learning that it is in the left half leaves the left half with probability 1/2.
   - [T] $p(x \mid y) = p(x, y) / p(y)$ when $p(y) > 0$.
   - [T] $X$ and $Y$ are independent when $p(x, y) = p(x)\,p(y)$.
   - [F] If $X$ and $Y$ are independent, knowing $Y$ changes the distribution of $X$.
4. We minimize a loss $A + \beta B$, with $A, B \ge 0$ and $\beta > 0$. What does a larger $\beta$ do? [[lecture_3#The information bottleneck]]
   - [x] It penalizes $B$ more, so the minimum moves toward a smaller $B$, even at the cost of a larger $A$
   - [ ] It penalizes $A$ more, so the minimum has a smaller $A$
   - [ ] Nothing, since multiplying a term by a constant does not change the minimum
   - [ ] It forces $A = 0$ at the minimum
5. Evaluate these statements about supervised learning: [[lecture_3#Inductive learning and information]] [[lecture_3#Compression implies generalization]] [[lecture_3#Deep networks can memorize]]
   - [T] A model generalizes when it performs well on new samples, not only on the training samples.
   - [F] A model with zero training error always generalizes.
   - [T] A linear classifier in the plane assigns the points on one side of a line to one class and the points on the other side to the other class.
   - [T] $N$ bits are enough to store $N$ binary labels.
6. In stochastic gradient descent with learning rate $\eta$ and batch size $B$, which statement is right? [[lecture_3#SGD noise limits information]] [[lecture_3#Invariance emerges from SGD]]
   - [ ] Each step computes the gradient on the whole dataset, and the noise comes from rounding errors
   - [ ] A larger $B$ gives a noisier gradient, since more samples bring more noise
   - [ ] The learning rate $\eta$ sets how many samples each step uses
   - [x] Each step computes the gradient on a random minibatch of $B$ samples, so a larger $B$ gives a less noisy gradient
