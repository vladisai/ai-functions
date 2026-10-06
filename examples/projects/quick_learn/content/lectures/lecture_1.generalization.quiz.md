# Learned

1. A puzzle solver can check any candidate solution against the rules while it searches. A spam filter trained on last year's emails labels a new email, and nobody tells it whether it was right until later. Which is which? [[lecture_1#Reward and loss]] [[lecture_1#Inductive vs. transductive inference]]
   - [ ] Both perform induction, since both rely on experience
   - [x] The puzzle solver performs transduction, the spam filter performs induction
   - [ ] The puzzle solver performs induction, the spam filter performs transduction
   - [ ] Both perform transduction, since both eventually see a loss
2. Evaluate these statements: [[lecture_1#Learning]] [[lecture_1#Reward and loss]] [[lecture_1#Inductive vs. transductive inference]]
   - [T] The "skill" that learning improves is the inference function, which maps future data onto decisions or actions.
   - [T] A test suite that returns only "pass" or "fail" on a model's code is a verifier, a loss that takes only two values.
   - [F] Learning can take place even if the effect of a decision never becomes manifest.
   - [F] Inductive inference needs no assumptions, explicit or implicit, once the training set is large enough.
3. Statistical learning can guarantee that the loss on future data is bounded. Under what condition, and what kind of guarantee is it? [[lecture_1#Statistical learning]] [[lecture_1#Generalization]]
   - [ ] Whatever the future data, it bounds the loss on each individual future datum
   - [ ] If the training loss is zero, it bounds the loss on future data from any distribution
   - [ ] If $P$ is known, it gives the exact loss on each future datum
   - [x] If future data is drawn from the same distribution $P$ as the training data, it bounds ensemble properties such as the expected loss
4. Evaluate these statements about the uniform generalization bound: [[lecture_1#Generalization]]
   - [T] Storing the dataset $D$ in the weights $w$ can make the training loss $L(w;D)$ zero, but makes the complexity term $R_D(w)$ large.
   - [T] Choosing zero weights, or a constant $f_w$, makes the complexity zero but pays a price in the loss.
   - [F] The bound is best minimized by driving the training loss to zero, whatever the complexity.
   - [F] The left-hand side, the expected loss on future data, can be computed once the training loss is known.
