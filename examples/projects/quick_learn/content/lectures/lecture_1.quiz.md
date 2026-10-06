# Prior

1. Evaluate these statements about training a model: [[lecture_1#Inductive vs. transductive inference]] [[lecture_1#Generalization]] [[lecture_1#The problem with induction]]
   - [T] A test datum is one that was not used to build the inference function.
   - [T] A held-out dataset is used to estimate performance on data that was not used for training.
   - [F] Overfitting means that a model fits its training data poorly.
   - [T] A prior or regularizer expresses a preference among solutions that the data alone does not determine.
2. Given $N$ samples $x_i \sim P$, $i = 1, \dots, N$, how do the average $\frac{1}{N}\sum_i \ell(x_i)$ and the expectation $\mathbb{E}_P \ell(x)$ relate? [[lecture_1#Statistical learning]] [[lecture_1#Generalization]]
   - [ ] They are always equal
   - [ ] The first needs $P$ to compute, the second can be computed from the samples
   - [x] The first is an empirical average computed from the samples drawn from $P$, the second is an expectation that needs $P$ to compute
   - [ ] Both can be computed exactly without knowing $P$
3. Evaluate these statements about mutual information: [[lecture_1#Generalization]]
   - [T] $I(A; B) = 0$ when $A$ and $B$ are independent.
   - [F] Mutual information can be negative.
   - [T] Larger $I(A; B)$ means that knowing $B$ tells more about $A$.
4. In Bayesian model averaging, how is a prediction formed? [[lecture_1#Optimal Transductive Inference (Solomonoff Induction)]]
   - [ ] By keeping only the model with the fewest parameters
   - [x] By averaging the predictions of all models, each weighted by its probability
   - [ ] By averaging only the models that fit the data worst
   - [ ] By picking one model uniformly at random
5. Evaluate these statements about programs and Turing machines: [[lecture_1#Uncertainty vs. time]] [[lecture_1#Optimal Transductive Inference (Solomonoff Induction)]] [[lecture_1#Levin's Universal Search]]
   - [T] A universal Turing machine can run any program given to it as input.
   - [F] Every program run on a Turing machine eventually halts.
   - [T] The elements of a countable set, such as the set of all programs, can be listed one after another, like the integers.
   - [F] Running many programs by interleaving their steps (dovetailing) requires each program to finish before the next one starts.
6. Evaluate these statements about dynamical systems and LLMs: [[lecture_1#LLMs as Maximalistic Models of Computation]]
   - [F] A dynamical system is a fixed table from inputs to outputs, with no state that evolves over time.
   - [T] An LLM generates text by sampling one token at a time, each conditioned on the tokens so far.
   - [F] When sampling at nonzero temperature, an LLM always returns the same output for the same prompt.
   - [T] A Turing machine run twice on the same input goes through the same steps.
