# Learned

1. A uniform generalization bound holds for any distribution $P$. Why does the lecture still find it suspicious? [[lecture_1#The problem with induction]]
   - [ ] The bound only holds for small training sets
   - [ ] The training loss on the right-hand side cannot be computed
   - [x] $P$ appears on both sides of the bound, so it must be the same $P$ in the past and forever after, an assumption of stationarity that is generally false for real data
   - [ ] The bound holds only when $P$ is known in advance
2. Evaluate these statements: [[lecture_1#The problem with induction]]
   - [F] Testing on a held-out dataset verifies that future data will come from the same distribution as past data.
   - [T] A finite dataset $D$ could have been drawn, with the same likelihood, from infinitely many distributions.
   - [F] Stationarity is a sound assumption for real data in finance, climate or language, as it is for dice.
   - [T] In the lecture's reading of Hume, a rationale for induction would require that unseen instances resemble seen ones and that nature is stationary, so there is none.
3. Evaluate these statements about transductive inference: [[lecture_1#Uncertainty vs. time]] [[lecture_1#Optimal Transductive Inference (Solomonoff Induction)]]
   - [T] It involves no uncertainty, since the quality of inference can be monitored along the way; the only question is how much time it takes.
   - [F] The inference function is fixed in advance and does not depend on the test datum.
   - [T] Solomonoff's algorithm keeps the programs that generate all the observed data bit by bit, then averages their next step weighted by the negative exponential of their length.
   - [F] Solomonoff's algorithm is optimal only when test data comes from the same distribution as training data.
4. Why have Solomonoff induction and Levin's universal search remained theoretical curiosities? [[lecture_1#Optimal Transductive Inference (Solomonoff Induction)]] [[lecture_1#Levin's Universal Search]]
   - [x] Solomonoff's procedure could take forever, since some programs may not terminate, and Levin's constant factor is the exponential of the length of the shortest optimal bespoke algorithm, which can be astronomical
   - [ ] Both are optimal only for data from the training distribution
   - [ ] Solomonoff's procedure ignores the length of programs, and Levin's search only works on NP-complete problems
   - [ ] Levin's constant factor grows with the size of each instance, and Solomonoff's procedure needs labeled data
