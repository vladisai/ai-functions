# Learned

1. When is a representation $Z$ minimal? [[lecture_3#Minimal representations are invariant]]
   - [ ] When it has the fewest dimensions
   - [ ] When $I(Z; X) = 0$
   - [x] When it is sufficient, $I(Z; T) = I(X; T)$, and has the smallest $I(Z; X)$ among the sufficient representations
   - [ ] When it keeps everything about the input
2. How can training with SGD lead to invariant representations? [[lecture_3#Invariance emerges from SGD]]
   - [ ] SGD adds explicit invariance constraints to the loss
   - [x] Weights stable to noise compute activations stable to noise, so the activations cannot carry much information about the input
   - [ ] SGD removes the nuisance variables from the training data
   - [ ] SGD makes the representation have fewer dimensions
3. Evaluate these statements: [[lecture_3#Minimal representations are invariant]] [[lecture_3#Semantic information]]
   - [T] A minimal sufficient representation is invariant to nuisances, since information about a nuisance is useless for the task, and keeping it would make the representation not minimal.
   - [F] To get a minimal representation, it is enough to give the state fewer dimensions.
   - [T] Under a uniform distribution, the 32-bit string '01' repeated 16 times and an irregular 32-bit string both cost 32 bits, though only the first has a short description.
   - [F] Shannon's definition lets a single string have information on its own, without a distribution.
