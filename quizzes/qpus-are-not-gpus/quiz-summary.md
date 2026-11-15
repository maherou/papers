# Quiz summary: QPUs Are Not GPUs: Why Quantum Processors Need Constant Classical Control

Generated 2026-11-13 by article-quiz skill v0.1 · 10 questions (9 single, 1 multi) · all quotes verified

## Themes

1. Where QPUs fit in scientific computing
2. Workloads where QPUs are not a consideration
3. The GPU offload model
4. The fighter-aircraft analogy
5. Why error correction is required
6. Syndrome measurements and decoding
7. The backlog problem
8. Layers of classical control
9. A reversal in the role of GPUs
10. A classical systems problem

## Questions

### q1 · single · Where QPUs fit in scientific computing
Where does the paper see the strongest case for quantum computing in science?
- **a. Simulating quantum systems themselves, such as molecules, materials, and catalysts** ✓
- b. Combinatorial optimization at practical problem sizes
- c. Solving large linear systems for typical scientific workloads
- d. Climate and weather modeling

> The strongest case is simulating quantum systems themselves: the electronic structure of molecules and materials, catalysts and battery chemistry, and strongly correlated physical systems (2 Where Quantum Processors Fit in Scientific Computing (p. 2))

### q2 · multi · Workloads where QPUs are not a consideration
For which of these workloads does the paper say QPUs are not a practical consideration on any planning horizon visible today? Select all that apply.
- **a. Computational fluid dynamics** ✓
- b. Electronic structure of molecules and materials
- **c. Climate and weather modeling** ✓
- **d. Structural mechanics** ✓
- e. Quantum dynamics and condensed-matter physics

> For most of today's scientific computing portfolio, including computational fluid dynamics, climate and weather modeling, structural mechanics, and classical molecular dynamics, QPUs are not a practical consideration on any planning horizon visible today. (2 Where Quantum Processors Fit in Scientific Computing (p. 2))

### q3 · single · The GPU offload model
In the familiar GPU offload model, what happens if the host is slow to respond?
- a. The results become unreliable and must be recomputed
- b. Running time grows exponentially as a backlog builds
- **c. The device sits idle and throughput suffers, but the results are still correct** ✓
- d. The kernel aborts and must be relaunched

> If the host is slow to respond, the device sits idle and throughput suffers, but the results it produces are still correct. (3 The Familiar Model: Accelerators as Offload Engines (p. 3))

### q4 · single · The fighter-aircraft analogy
Which aircraft does the paper say a QPU most resembles?
- **a. An unstable fighter that needs a flight control computer making continuous corrections** ✓
- b. A stable airliner that keeps flying straight and level if the pilot lets go
- c. A glider that needs no power once it is aloft
- d. A drone flown entirely from a remote ground station

> A QPU is much closer to the fighter than to the airliner. (4 A Device That Cannot Fly Itself (p. 3))

### q5 · single · Why error correction is required
Why does useful quantum computation require quantum error correction?
- a. Classical decoders introduce errors that must be removed
- b. Measuring a qubit always destroys the whole computation
- c. QPUs cannot be shielded from the heat of nearby GPUs
- **d. The best two-qubit operations fail roughly once in a few hundred to a thousand attempts** ✓

> Across the leading qubit technologies, the best two-qubit operations now fail roughly once in every few hundred to a thousand attempts (4 A Device That Cannot Fly Itself (p. 3))

### q6 · single · Syndrome measurements and decoding
What do syndrome measurements do in quantum error correction?
- a. They read out the final answer of the computation
- **b. They reveal errors without disturbing the encoded information** ✓
- c. They apply corrections directly to each physical qubit
- d. They copy the quantum state to classical memory as a backup

> The device repeatedly measures a set of checks across its physical qubits, called syndrome measurements, which reveal errors without disturbing the encoded information. (4 A Device That Cannot Fly Itself (p. 4))

### q7 · single · The backlog problem
What happens if the classical decoder cannot keep up with the quantum device?
- a. The device idles, but its results remain correct
- b. The QPU switches to a slower, error-free mode
- **c. Unprocessed syndrome data accumulates, delays compound, and runtime can grow exponentially** ✓
- d. The computation finishes on time but with lower precision

> Because each dependent step must wait for the backlog to clear, delays compound, and runtime can grow exponentially with the number of such steps. (4 A Device That Cannot Fly Itself (p. 4))

### q8 · single · Layers of classical control
The classical side of a quantum system is a stack of layers on different timescales. What do the inner layers demand?
- a. Remote access through job submission, like other HPC resources
- b. Only occasional host attention, as with a GPU kernel
- c. Large shared-memory nodes in a separate data center
- **d. Deterministic, low-latency classical computing physically close to the quantum device** ✓

> The inner layers demand deterministic, low-latency classical computing physically close to the quantum device. (5 Layers of Classical Control (p. 4))

### q9 · single · A reversal in the role of GPUs
What "interesting reversal" does the paper point out about GPUs?
- a. QPUs are likely to replace GPUs as the main accelerator in HPC nodes
- **b. GPUs may find a growing role inside the quantum control system, serving the QPU** ✓
- c. GPU programming models already support hard real-time co-execution with QPUs
- d. GPUs are becoming too slow to host quantum workloads

> The device that defined the offload model may find a growing role inside the quantum control system, serving the QPU rather than the other way around. (6 Implications and Outlook (p. 5))

### q10 · single · A classical systems problem
What is the paper's main conclusion for system architects and facility planners?
- a. A QPU can be integrated as one more accelerator in the node, with a thin driver layer
- b. Quantum devices should be reached only remotely, away from HPC systems
- **c. Integrating quantum computing into HPC is as much a classical systems problem as a quantum one** ✓
- d. Facilities should wait until qubit error rates fall before planning any integration

> What seems clear is that integrating quantum computing into HPC is as much a classical systems problem as a quantum one (6 Implications and Outlook (p. 6))
