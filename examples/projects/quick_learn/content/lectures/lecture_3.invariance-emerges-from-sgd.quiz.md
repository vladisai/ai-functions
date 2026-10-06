# Prior

1. Why does SGD noise limit the information in the weights?
   - [ ] The noise erases the training data
   - [ ] The noise makes the network smaller
   - [x] The weights can only keep details that survive the noise
   - [ ] The noise makes the loss zero
2. Evaluate these statements:
   - [T] A representation that carries information about a nuisance is not minimal.
   - [F] A minimal sufficient representation keeps everything about the input.

# Learned

1. How can training with SGD lead to invariant representations?
   - [x] Weights stable to noise compute activations stable to noise, so the activations cannot carry much information about the input
   - [ ] SGD adds explicit invariance constraints to the loss
   - [ ] SGD removes the nuisance variables from the training data
   - [ ] SGD makes the representation have fewer dimensions
2. Evaluate these statements:
   - [T] Rewordings of a sentence map to nearby points in $Z$, while an unrelated sentence maps elsewhere.
   - [F] Invariance can only come from being built into the architecture.
   - [T] A model learns to be invariant to rewording because the exact wording does not help to predict, and the weights cannot afford to store it.
