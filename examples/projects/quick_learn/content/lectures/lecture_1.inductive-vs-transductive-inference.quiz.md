# Prior

1. In this lecture, what does a loss function do?
   - [x] It returns a number for every decision or action, measuring the effect of that outcome
   - [ ] It returns the probability of each input
   - [ ] It maps past data onto the weights of a model
   - [ ] It selects which data goes into the training set
2. Evaluate these statements about training and test data:
   - [T] A test datum is one that was not used to build the inference function.
   - [T] A prior or regularizer expresses a preference among solutions that the data alone does not determine.

# Learned

1. A puzzle solver can check any candidate solution against the rules while it searches. A spam filter trained on last year's emails labels a new email, and nobody tells it whether it was right until later. Which is which?
   - [x] The puzzle solver performs transduction, the spam filter performs induction
   - [ ] Both perform induction, since both rely on experience
   - [ ] The puzzle solver performs induction, the spam filter performs transduction
   - [ ] Both perform transduction, since both eventually see a loss
2. Evaluate these statements:
   - [T] In transduction, the best outcome can be found empirically by evaluating the loss on candidate outcomes, even without a formula for the loss.
   - [F] Inductive inference needs no assumptions once the training set is large enough.
   - [T] In induction, the quality of inference depends on how the past (training) data relates to the future (test) data.
3. Where does the "inductive bias" come from?
   - [x] From choices such as the prior, regularizer or hypothesis behind the design of the learning process, often implicit
   - [ ] From the loss function evaluated at test time
   - [ ] From errors in the training labels
   - [ ] It exists only when the designer adds it explicitly
