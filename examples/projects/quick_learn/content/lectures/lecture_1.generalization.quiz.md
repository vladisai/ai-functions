# Prior

1. Given $N$ samples $x_1, \dots, x_N$ drawn from $P$, how do $\frac{1}{N}\sum_i \ell(x_i)$ and $\mathbb{E}_P \ell(x)$ relate?
   - [x] The first is an empirical average computed from the samples, the second is an expectation that needs $P$ to compute
   - [ ] They are always equal
   - [ ] The first needs $P$ to compute, the second can be computed from the samples
   - [ ] Both can be computed exactly without knowing $P$
2. Evaluate these statements about mutual information:
   - [T] $I(A; B) = 0$ when $A$ and $B$ are independent.
   - [F] Mutual information can be negative.
   - [T] Larger $I(A; B)$ means that knowing $B$ tells more about $A$.

# Learned

1. A model has a training error of 2% and an expected error on future data of 15%. What is its generalization gap?
   - [ ] 2%
   - [x] 13%
   - [ ] 15%
   - [ ] 17%
2. Which statement about the terms of the uniform generalization bound is correct?
   - [x] The left-hand side, the expected loss on future data, cannot be computed because $P$ is unknown
   - [ ] The training loss $L(w;D)$ cannot be computed, because it averages over unseen data
   - [ ] The left-hand side becomes computable once the training loss is zero
   - [ ] The training loss is fixed by the data and cannot be changed by training
3. Evaluate these statements:
   - [T] Storing the dataset $D$ in the weights $w$ can make the training loss zero, but makes the complexity term $R_D(w)$ large.
   - [T] Choosing zero weights, or a constant $f_w$, makes the complexity zero but pays a price in the loss.
   - [F] The bound is best minimized by driving the training loss to zero, whatever the complexity.
   - [F] A uniform generalization bound holds only for one specific, known distribution $P$.
