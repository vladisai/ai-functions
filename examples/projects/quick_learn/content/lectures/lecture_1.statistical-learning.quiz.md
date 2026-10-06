# Prior

1. What does $(x_i, y_i) \sim P$ say?
   - [x] The pair $(x_i, y_i)$ is a sample drawn from the distribution $P$
   - [ ] $x_i$ and $y_i$ are approximately equal under $P$
   - [ ] $P$ is computed from the pair $(x_i, y_i)$
   - [ ] $y_i$ is the probability of $x_i$
2. Evaluate these statements about inductive inference:
   - [T] The loss on the present test datum is not available when the decision is made.
   - [F] The training data and the test datum are the same data.

# Learned

1. In classical machine learning, what is inferred from the training set $D$?
   - [ ] The test data $x$
   - [x] The weights $w$ of a function $f_w$ that is later used for inference on new data
   - [ ] The loss function $\ell$
   - [ ] The set of possible decisions
2. Evaluate these statements:
   - [T] Inductive inference involves uncertainty, because the outcome of a decision is known only after it has been rendered.
   - [F] The guarantees of statistical learning still hold when future data comes from a different distribution than the training data.
   - [T] The distribution $P$ that the data is assumed to be drawn from is unknown.
3. What kind of guarantee does statistical learning give about future inference?
   - [x] Ensemble properties of its outcome, such as a bound on the loss
   - [ ] The exact loss on each individual future datum
   - [ ] A bound on the time it takes to find a decision
   - [ ] A guarantee that the training loss is zero
