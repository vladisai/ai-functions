## About this material

These are the lecture notes of a class on AI agents: [[lectures/lecture_1|Lecture 1]] (Stefano Soatto) on why learning for agents is about reducing the time to solve new tasks rather than about generalization, [[lectures/lecture_2|Lecture 2]] (Alessandro Achille) on LLMs and agents as stochastic dynamical systems to be controlled, and [[lectures/lecture_3|Lecture 3]] (Alessandro Achille) on Shannon information, compression and inductive learning. The lectures build on each other, so point back to the earlier one when a reader is missing an idea it introduced.

## Pre-conditions

- **Basic machine learning**: training and test sets, weights, loss, overfitting, regularization.
- **Probability**: random variables, sampling $x \sim P$, expectation, conditional distributions $p(\cdot \mid x)$. Lecture 3 also uses $\log$ and sums over distributions.
- **Computation, at the level of the idea**: what a Turing machine and a program are, and that some programs never halt. Lecture 1 explains the rest.
- **LLMs as users see them**: prompts, tokens, sampling, tool calls. No knowledge of transformer internals is needed.

If a reader is missing probability, point them to the book's [[book/probability/chapter|probability primer]].

## Post-conditions

- **Lecture 1**: tell transductive inference (loss available during inference) from inductive inference (blind, based on past data); read the uniform generalization bound and explain the trade-off between training loss and complexity; explain why the same-distribution assumption is unverifiable and why Hume found no rationale for induction; explain Solomonoff induction, Levin search and its exponential constant, and Solomonoff's 1984 point that learning reduces that constant; explain why LLMs are maximalistic, stochastic computers that a prompt can condition but not control; tell generality from generalization.
- **Lecture 2**: model an LLM as a stochastic dynamical system with state $x_t$, transitions $x_{t+1} \sim p(\cdot \mid x_t)$ and controls $u_t$ from a policy $\pi$; read the KV cache as the state; describe agents with actions $a_t$, observations $o_t$, rewards $R(\tau)$ and costs $c(x_t, u_t)$.
- **Lecture 3**: compute entropy and mutual information for simple distributions, relate entropy to optimal code length and learning to compression, apply the data processing inequality, and explain the information bottleneck, compression bounds on generalization, and invariance of minimal representations.

## Topic dependencies

- Transduction vs. induction (Lecture 1) frames everything else in the class.
- The uniform generalization bound depends on expectation and on mutual information $I_P(w; D)$, which Lecture 3 defines.
- Levin search depends on Solomonoff induction, and Solomonoff's 1984 observation depends on Levin's constant.
- "LLMs as stochastic dynamical systems" in Lecture 1 is made precise in Lecture 2.
- The compression view of generalization in Lecture 3 revisits the bound and the trade-off of Lecture 1.

## Common misconceptions

- Thinking transduction needs no computation: there is no uncertainty, but the cost is time.
- Thinking a uniform generalization bound frees us from assumptions: $P$ is unknown but must be the same in the past and the future.
- Reading "generality" as "generalization": generality is universality, solving any task, possibly unforeseen.
- Thinking a prompt, a "skill" file or the chain-of-thought is a program that controls an LLM: it only conditions a stochastic system.
- Thinking Solomonoff induction or Levin search are practical as stated: one may never terminate, the other has an astronomical constant.
- Thinking an LLM is universal because its weights could implement a Turing machine: the point is universality as a stochastic dynamical system.

## Style

The lectures are a class's notes, so a rewrite stays close to the lecture: keep the lecturer's notation (e.g. $D$, $w$, $f_w$, $\ell$, $L(w;D)$, $R_D(w)$ in Lecture 1; $x_t$, $u_t$, $\pi$, $p_w$ in Lecture 2; $H(X)$, $I(X;Y)$ in Lecture 3), the lecturer's terms, the order of the sections and their headings. Keep every figure, its caption and every iframe exactly as they are, and keep the footnotes and references. Adapt the explanation to the reader: add intuition, a worked example or a short recap of a missing prerequisite where their quiz answers or questions show a gap, and shorten what they already know. Do not add claims the lecture does not make, and do not soften its positions (e.g. Lecture 1's critique of induction). Link between lectures with wikilinks such as [[lectures/lecture_2|Lecture 2]]. The learned quizzes test what each section teaches, and the prior quizzes test its prerequisites, often an earlier section.
