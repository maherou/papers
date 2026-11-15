# Quiz summary: A Better Lesson: Staying on the Right Side of Scale

Generated 2026-11-13 by article-quiz skill v0.1 · 10 questions (8 single, 2 multi) · all quotes verified

## Themes

1. Sutton's bitter lesson
2. Sandcastles and boats
3. Four principles for the right side of scale
4. Ground truth as a strategic asset
5. Making knowledge legible
6. Reinforcement learning needs a trustworthy signal
7. Verification versus validation
8. Verification checks that computation can settle
9. Where expert attention goes
10. A practical test for technical leaders

## Questions

### q1 · single · Sutton's bitter lesson
What was Rich Sutton's observation in "The Bitter Lesson"?
- a. Algorithmic ingenuity, more than faster hardware, has produced the biggest gains in AI
- **b. General methods that scale with computation have repeatedly overtaken approaches built on encoded human knowledge** ✓
- c. Carefully encoded expert knowledge eventually beats general methods once enough data is collected
- d. AI research made little real progress in its first seventy years

> general methods that scale with computation, chiefly search and learning, have repeatedly overtaken approaches built on carefully encoded human knowledge. (Overview (p. 1))

### q2 · single · Sandcastles and boats
In the paper's rising-tide picture, which of these is a sandcastle?
- **a. A kernel tuned for one generation of hardware** ✓
- b. A regression suite with reference solutions
- c. A performance-portable library
- d. Documented design rationale

> A kernel tuned for one generation of hardware, a heuristic that replaces a search the machine could now perform, or tacit knowledge that lives only in a few experts’ heads all fall into this category. (Two Kinds of Investment (p. 2))

### q3 · multi · Four principles for the right side of scale
Which of these are among the paper's four principles for staying on the right side of scale? Select all that apply.
- **a. Build on what scales** ✓
- b. Encode expert knowledge directly into solvers
- **c. Anchor in ground truth** ✓
- **d. Reserve people for judgment** ✓
- e. Automate validation before verification

> We propose four principles for staying on the right side of scale: build on what scales, anchor in ground truth, make knowledge legible, and reserve people for judgment. (Abstract (p. 1))

### q4 · single · Ground truth as a strategic asset
Under the paper's reading, what do test suites, reference solutions, validated datasets, and benchmarks become?
- a. Quality overhead that AI tools will make unnecessary
- b. Sandcastles that erode with each hardware generation
- **c. Strategic assets, because every new solution, human or AI, will be judged against them** ✓
- d. A substitute for expert judgment about which problems matter

> Test suites, reference solutions, validated datasets, and benchmarks are often treated as quality overhead. Under this reading, they become strategic assets. (Four Principles for the Right Side of Scale (p. 3))

### q5 · single · Making knowledge legible
Why does the paper urge organizations to make their knowledge legible?
- a. So experts can hand-encode solutions more precisely
- b. Because readable code runs faster on new hardware
- c. So that test suites become less necessary
- **d. Because AI tools cannot recover intent that exists only in someone's memory** ✓

> AI tools can read source code, documentation, and specifications, but they cannot recover intent that exists only in someone’s memory. (Four Principles for the Right Side of Scale (p. 3))

### q6 · single · Reinforcement learning needs a trustworthy signal
Reinforcement learning depends on a reliable way to tell whether an attempt succeeded. What risk does the paper see in training against weak checks?
- a. The system learns more slowly but reaches the same result
- b. The system stops improving once it matches human experts
- **c. The system can learn to satisfy the checker without solving the problem** ✓
- d. The system needs human games or examples to learn from

> A system trained against weak checks can learn to satisfy the checker without solving the problem, so a thin test suite produces misleading rewards. (Reinforcement Learning as the Linchpin (p. 4))

### q7 · single · Verification versus validation
Which pairing matches the paper's shorthand for verification and validation?
- a. Verification: solving the right equations. Validation: solving the equations right.
- **b. Verification: solving the equations right. Validation: solving the right equations.** ✓
- c. Verification: human code review. Validation: automated testing.
- d. Verification: checking performance. Validation: checking portability.

> The common shorthand is that verification means solving the equations right, and validation means solving the right equations. (Verification Versus Validation (p. 4))

### q8 · multi · Verification checks that computation can settle
Which of these does the paper list as checks that produce the automatic, repeatable signal reinforcement learning needs? Select all that apply.
- **a. Manufactured solutions** ✓
- b. Experimental and observational data
- **c. Convergence studies** ✓
- **d. Regression tests** ✓
- e. Physical insight about model adequacy

> Manufactured solutions, convergence studies, conservation checks, regression tests, and comparisons against reference results all produce the automatic, repeatable signal reinforcement learning needs. (Verification Versus Validation (p. 4))

### q9 · single · Where expert attention goes
As AI absorbs more verification work, where does the paper expect expert attention to concentrate?
- **a. On validation: what a model must capture, what evidence is sufficient, and when a result can be trusted** ✓
- b. On verification, because it is the hardest part of the work to automate
- c. On hand-tuning kernels for each new hardware generation
- d. On replacing reference datasets with AI-generated ones

> As AI absorbs more verification work, expert attention is likely to concentrate on validation: deciding what a model must capture, what evidence is sufficient, and when a result is trustworthy enough to act on. (Verification Versus Validation (p. 5))

### q10 · single · A practical test for technical leaders
What practical test does the paper offer technical leaders reviewing a software portfolio?
- a. Ask whether each effort could be done by an AI agent today, and cancel any that could
- **b. Ask whether each effort makes the domain more verifiable, legible, or scalable, or encodes an answer a machine might find** ✓
- c. Ask whether each effort has been optimized for the newest hardware generation
- d. Ask whether each effort has been validated against experimental data

> for each major effort, ask whether it makes the domain more verifiable, more legible, or more scalable, or whether it encodes an answer that a future machine might find on its own. (Implications and Outlook (p. 5))
