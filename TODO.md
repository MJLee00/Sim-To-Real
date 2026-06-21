# Suggested Revision: Extending OverFlowLight toward Sim-to-Real Overflow Control

## 1. Overall Revision Direction

The current paper already provides a strong real-world system contribution by proposing OverFlowLight, a real-time overflow detection and phase-selection framework for urban traffic signal control. However, the current version mainly relies on field deployment and argues that existing simulators cannot accurately reproduce overflow scenarios. To further strengthen the paper, I suggest extending it toward a **real-calibrated sim-to-real overflow-control framework**.

The revised paper can position OverFlowLight not only as a deployed overflow-control system, but also as a bridge between simulation-based traffic signal learning and real-world deployment. The key idea is to construct a simulator calibrated by real-world traffic data, use it for safe training and stress testing, and then validate the learned or tuned controller under real replay, shadow-mode deployment, or real-world operation.

A possible revised title could be:

**OverFlowLight-S2R: Real-Calibrated Sim-to-Real Overflow Control for Urban Traffic Signal Systems**

The revised contribution can be summarized as follows:

1. We construct a real-calibrated overflow simulator that explicitly models spillback, exit-lane capacity, lane imbalance, perception noise, and signal actuation delay.
2. We propose an OPM-constrained sim-to-real transfer mechanism that restricts both simulated and real-world actions to overflow-mitigating phase sets.
3. We provide theoretical analysis of the simulator-to-real performance gap and the safety benefit of OPM-constrained action masking.
4. We validate the framework through simulator fidelity evaluation, sim-to-real transfer experiments, cross-intersection generalization, and robustness stress tests.

---

## 2. Theoretical Extension

### 2.1 OPM-Constrained Safe MDP Formulation

The current theoretical analysis mainly discusses Q-learning convergence under the OPM-constrained action space. This can be extended into a constrained Markov Decision Process formulation.

We can define the overflow-aware traffic signal control problem as:

[
\mathcal{M} = (\mathcal{S}, \mathcal{A}, P, r, c, \gamma)
]

where:

* (\mathcal{S}) is the traffic state space;
* (\mathcal{A}) is the original signal phase action space;
* (P) is the traffic transition function;
* (r(s,a)) is the efficiency reward, such as negative queue length or negative delay;
* (c(s,a)) is the overflow risk cost;
* (\gamma) is the discount factor.

The Overflow Phase Map defines a state-dependent safe action set:

[
\mathcal{A}_{OPM}(s) \subseteq \mathcal{A}
]

The OPM-constrained policy satisfies:

[
\pi(a|s)=0, \quad \forall a \notin \mathcal{A}_{OPM}(s)
]

This formulation allows us to describe OverFlowLight as a safety-constrained control interface rather than only a heuristic phase mask. The main theoretical claim can be:

**Proposition 1.** If the overflow direction is correctly detected and the OPM contains at least one overflow-mitigating phase for each detected overflow direction, then an OPM-constrained policy avoids unsafe phase choices that do not contribute to overflow mitigation.

This proposition highlights that OPM is not only an engineering module, but also a safety-preserving action-space reduction mechanism.

---

### 2.2 Sim-to-Real Performance Gap Bound

To support the sim-to-real extension, we can define two MDPs:

[
\mathcal{M}_S = (\mathcal{S}, \mathcal{A}, P_S, r_S, \gamma)
]

[
\mathcal{M}_T = (\mathcal{S}, \mathcal{A}, P_T, r_T, \gamma)
]

where (\mathcal{M}_S) denotes the source simulation environment and (\mathcal{M}_T) denotes the target real-world environment.

Assume the reward and transition gaps are bounded:

[
|r_T(s,a)-r_S(s,a)| \leq \epsilon_r
]

[
|P_T(\cdot|s,a)-P_S(\cdot|s,a)|_1 \leq \epsilon_P
]

Then for any policy (\pi), the value gap can be bounded as:

[
|V_T^\pi(s)-V_S^\pi(s)|
\leq
\frac{\epsilon_r}{1-\gamma}
+
\frac{\gamma R_{\max}\epsilon_P}{(1-\gamma)^2}
]

This bound directly supports the motivation for real-calibrated simulation. If the calibrated simulator reduces (\epsilon_r) and (\epsilon_P), then the sim-to-real performance gap becomes smaller.

For overflow control, we can further define an overflow cost function (c(s,a)), and derive:

[
|J_T^{overflow}(\pi)-J_S^{overflow}(\pi)|
\leq
\frac{\epsilon_c}{1-\gamma}
+
\frac{\gamma C_{\max}\epsilon_P}{(1-\gamma)^2}
]

This provides a theoretical explanation for why better simulation fidelity should improve real-world overflow-control reliability.

---

### 2.3 Robust Domain Randomization Objective

To improve robustness under real-world uncertainty, simulator parameters can be represented as:

[
\xi \in \Xi
]

where (\xi) includes traffic demand, turning ratio, exit-lane capacity, perception noise, weather condition, driver behavior, and signal actuation delay.

The robust training objective can be written as:

[
\pi^* =
\arg\min_{\pi}
\max_{\xi \in \Xi}
\mathbb{E}*{\mathcal{M}*{\xi}, \pi}
[
L_{delay} + \lambda L_{overflow}
]
]

Alternatively, the problem can be formulated as a constrained optimization problem:

[
\min_\pi J_{delay}(\pi)
]

[
\text{s.t.} \quad J_{overflow}(\pi) \leq \delta
]

This formulation shows that the controller is optimized not only for average efficiency, but also for worst-case overflow safety. The paper can claim that OPM-constrained domain randomization improves transfer robustness because the policy is trained under diverse simulated conditions while being restricted to feasible overflow-mitigating actions.

---

## 3. Experimental Extension

### 3.1 Experiment 1: Real-Calibrated Simulator Fidelity

The first new experiment should evaluate whether the calibrated simulator can reproduce real-world overflow dynamics more accurately than standard simulators.

#### Goal

To demonstrate that the proposed calibrated simulator better matches real-world traffic overflow patterns than default SUMO or CityFlow.

#### Compared environments

| Environment             | Description                                        |
| ----------------------- | -------------------------------------------------- |
| Default SUMO / CityFlow | Standard simulator without overflow calibration    |
| Calibrated OverflowSim  | Simulator calibrated using real-world traffic data |
| Real-world logs         | Real traffic observations used as reference        |

#### Calibration factors

The simulator should be calibrated using:

* arrival demand;
* turning ratio;
* saturation flow;
* exit-lane capacity;
* queue spillback threshold;
* lane mismatch;
* signal lost time;
* perception noise;
* signal actuation delay.

#### Metrics

| Metric                          | Purpose                            |
| ------------------------------- | ---------------------------------- |
| Queue length distribution error | Measures queue-level fidelity      |
| Overflow count error            | Measures overflow-event fidelity   |
| Overflow duration error         | Measures temporal fidelity         |
| Speed distribution error        | Measures mobility-pattern fidelity |
| Throughput error                | Measures efficiency fidelity       |
| Phase-switch timing error       | Measures control-response fidelity |

#### Expected conclusion

The calibrated simulator should show lower distributional error and lower overflow-count error than the default simulator. This experiment provides the foundation for all subsequent sim-to-real transfer claims.

---

### 3.2 Experiment 2: Sim-to-Real Transfer Performance

The second experiment should test whether policies trained or tuned in simulation can transfer to real-world traffic scenarios.

#### Goal

To evaluate whether real-calibrated simulation improves real-world overflow control after transfer.

#### Compared methods

| Method                                      | Description                                                    |
| ------------------------------------------- | -------------------------------------------------------------- |
| Real-only                                   | Trained or tuned only with real-world data                     |
| Default Sim                                 | Trained in default simulator and transferred to real replay    |
| Calibrated Sim                              | Trained in calibrated simulator and transferred to real replay |
| Calibrated Sim + Domain Randomization       | Trained with randomized traffic and sensor parameters          |
| Calibrated Sim + OPM                        | Uses OPM-constrained action masking during transfer            |
| Calibrated Sim + Domain Randomization + OPM | Full proposed sim-to-real framework                            |

#### Real-world test settings

* real traffic replay;
* shadow-mode evaluation;
* held-out real intersections;
* real deployment if available.

#### Metrics

| Metric                  | Direction        |
| ----------------------- | ---------------- |
| Overflow count          | Lower is better  |
| Overflow duration       | Lower is better  |
| Overflow Switch Success | Higher is better |
| Throughput              | Higher is better |
| Stop frequency          | Lower is better  |
| Average delay           | Lower is better  |
| Safety violation rate   | Lower is better  |

#### Expected conclusion

The full method should achieve the best safety-performance trade-off. In particular, OPM should significantly reduce unsafe transfer behavior, while calibration and domain randomization should reduce the simulator-to-real gap.

---

### 3.3 Experiment 3: Cross-Intersection and Cross-City Generalization

The third experiment should evaluate whether the proposed method generalizes beyond the intersections used for calibration or training.

#### Goal

To demonstrate that the method is not overfitted to a small number of deployed intersections.

#### Settings

| Setting                        | Description                                                                        |
| ------------------------------ | ---------------------------------------------------------------------------------- |
| Seen city, unseen intersection | Train on several intersections and test on held-out intersections in the same city |
| Cross-city transfer            | Train on one city and test on another city                                         |
| Cross-structure transfer       | Test on intersections with different lane configurations                           |
| Severe lane mismatch           | Test on intersections with unbalanced entry and exit capacities                    |

#### Few-shot calibration setting

The target intersection can be calibrated using different amounts of real data:

| Calibration data | Description                        |
| ---------------- | ---------------------------------- |
| Zero-shot        | No target-intersection calibration |
| 1 day            | Minimal target data                |
| 3 days           | Short-term calibration             |
| 1 week           | Stronger target calibration        |

#### Expected conclusion

The full method should perform well in zero-shot settings and improve further with a small amount of target-intersection calibration. This would support the claim that OverFlowLight-S2R is scalable and transferable.

---

### 3.4 Experiment 4: Domain Gap and Robustness Stress Test

The fourth experiment should evaluate robustness under realistic sim-to-real gaps.

#### Goal

To test whether the controller remains safe and effective under traffic, perception, and actuation uncertainty.

#### Perturbation types

| Domain gap         | Perturbation                                           |
| ------------------ | ------------------------------------------------------ |
| Demand gap         | Increase peak demand by 20%, 40%, and 60%              |
| Turning-ratio gap  | Shift left/straight/right movement ratios              |
| Capacity gap       | Reduce exit-lane capacity                              |
| Sensor noise       | Add radar noise and camera detection errors            |
| Sensor missingness | Randomly remove vehicle observations                   |
| Weather gap        | Simulate rain, snow, fog, and nighttime degradation    |
| Actuation delay    | Add 0.1s, 0.5s, and 1s signal command delay            |
| Incident gap       | Simulate downstream blockage or temporary lane closure |

#### Metrics

* overflow count;
* safety violation rate;
* throughput degradation;
* recovery time after overflow;
* policy stability;
* phase-switch frequency.

#### Expected conclusion

The full OPM-constrained sim-to-real method should be more robust than ordinary RL-based controllers, especially under perception noise, exit-capacity reduction, and sudden demand surges.

---

## 4. Suggested New Experimental Questions

The experiment section can be reorganized around the following research questions:

### RQ1: Can a real-calibrated simulator reproduce real-world overflow dynamics?

This question evaluates simulator fidelity by comparing calibrated simulation with real-world logs.

### RQ2: Does simulation-trained overflow control transfer to real-world traffic?

This question evaluates sim-to-real performance using real replay, shadow-mode testing, or real deployment.

### RQ3: How much real data is needed to adapt the controller to a new intersection?

This question evaluates zero-shot and few-shot transfer.

### RQ4: Does OPM-constrained action masking reduce unsafe transfer behavior?

This question evaluates the role of OPM as a safety-preserving transfer mechanism.

### RQ5: How robust is the transferred controller under domain gaps?

This question evaluates robustness under demand shifts, perception noise, weather degradation, capacity changes, and signal actuation delay.

---

## 5. Suggested Writing for the Method Section

A new subsection can be added after the current overflow phase selection module.

### Real-Calibrated Sim-to-Real Overflow Learning

To bridge the gap between simulation-based training and real-world overflow control, we extend OverFlowLight with a real-calibrated sim-to-real learning framework. Unlike standard traffic simulators, which often fail to reproduce severe spillback and intersection gridlock, our simulator explicitly models exit-lane capacity, lane imbalance, queue spillback, perception noise, and signal actuation delay using real-world deployment data.

The proposed framework consists of three components. First, we calibrate the simulator using real traffic observations, including arrival demand, turning ratios, saturation flow, queue length distribution, and overflow duration. Second, we train or tune the traffic signal controller in the calibrated simulator under domain-randomized traffic and sensing conditions. Third, we transfer the learned controller to real-world replay or deployment through the OPM-constrained action interface, which restricts unsafe phase choices and preserves overflow-mitigation feasibility.

This design allows OverFlowLight to support safe policy training, systematic stress testing, and scalable deployment to unseen intersections.

---

## 6. Suggested Writing for the Theory Section

A new theoretical section can be added to formalize sim-to-real transfer.

### Sim-to-Real Gap under OPM-Constrained Control

We model the simulation environment and the real-world environment as two MDPs with different transition and reward functions. The simulation MDP is denoted by (\mathcal{M}_S), while the real-world MDP is denoted by (\mathcal{M}_T). The performance gap between the two environments depends on the reward discrepancy and transition discrepancy.

If the reward error is bounded by (\epsilon_r) and the transition error is bounded by (\epsilon_P), then the value difference of any policy (\pi) can be bounded by:

[
|V_T^\pi(s)-V_S^\pi(s)|
\leq
\frac{\epsilon_r}{1-\gamma}
+
\frac{\gamma R_{\max}\epsilon_P}{(1-\gamma)^2}
]

This result indicates that reducing simulator-reality discrepancies through real-world calibration can directly reduce the transfer gap.

Furthermore, the OPM-constrained action set reduces the effective action space from (\mathcal{A}) to (\mathcal{A}_{OPM}(s)). This prevents the controller from selecting phases that are irrelevant or unsafe under detected overflow states. Therefore, the OPM not only improves control efficiency, but also provides a safety-preserving mechanism for sim-to-real transfer.

---

## 7. Suggested Writing for the Experiment Section

A new experimental subsection can be added.

### Sim-to-Real Transfer Evaluation

We evaluate whether OverFlowLight can be extended from a real-world overflow-control system into a sim-to-real learning framework. Specifically, we construct a real-calibrated overflow simulator using field data collected from deployed intersections. The simulator models arrival demand, turning ratio, exit-lane capacity, spillback threshold, perception noise, and signal actuation delay.

We compare five training and transfer settings: default simulation, calibrated simulation, calibrated simulation with domain randomization, calibrated simulation with OPM constraints, and the full calibrated simulation with both domain randomization and OPM constraints. The transferred controllers are evaluated on real traffic replay and held-out intersections.

The results are expected to demonstrate that real calibration significantly improves simulator fidelity, domain randomization improves robustness, and OPM-constrained transfer substantially reduces unsafe phase choices under overflow conditions.

---

## 8. Most Important New Tables

### Table A: Simulator Fidelity

| Environment            | Queue Error ↓ | Overflow Count Error ↓ | Speed Distribution Error ↓ | Throughput Error ↓ |
| ---------------------- | ------------: | ---------------------: | -------------------------: | -----------------: |
| Default SUMO           |               |                        |                            |                    |
| Default CityFlow       |               |                        |                            |                    |
| Calibrated OverflowSim |               |                        |                            |                    |

### Table B: Sim-to-Real Transfer

| Method               | Overflow Count ↓ | OSS ↑ | Throughput ↑ | Stops ↓ | Safety Violation ↓ |
| -------------------- | ---------------: | ----: | -----------: | ------: | -----------------: |
| Default Sim          |                  |       |              |         |                    |
| Calibrated Sim       |                  |       |              |         |                    |
| Calibrated Sim + DR  |                  |       |              |         |                    |
| Calibrated Sim + OPM |                  |       |              |         |                    |
| Full Method          |                  |       |              |         |                    |

### Table C: Cross-Intersection Transfer

| Target Setting                 | Zero-shot | 1-day Calibration | 3-day Calibration | 1-week Calibration |
| ------------------------------ | --------: | ----------------: | ----------------: | -----------------: |
| Seen city, unseen intersection |           |                   |                   |                    |
| New city                       |           |                   |                   |                    |
| Severe lane mismatch           |           |                   |                   |                    |

### Table D: Robustness under Domain Gaps

| Perturbation            | Baseline RL | Calibrated Sim | Full Method |
| ----------------------- | ----------: | -------------: | ----------: |
| Demand +20%             |             |                |             |
| Demand +40%             |             |                |             |
| Demand +60%             |             |                |             |
| Sensor noise            |             |                |             |
| Sensor missingness      |             |                |             |
| Exit capacity reduction |             |                |             |
| Actuation delay         |             |                |             |

---

## 9. Summary of Key Revision Advice

The strongest revision strategy is to avoid presenting simulation as a weak supplementary experiment. Instead, simulation should become a structured sim-to-real contribution. The paper should argue that standard simulators are insufficient for overflow control, and then propose a real-calibrated overflow simulator as a solution.

The most important additions are:

1. Add a real-calibrated overflow simulator.
2. Add sim-to-real transfer experiments.
3. Add cross-intersection and cross-city generalization.
4. Add robustness tests under domain gaps.
5. Add a theoretical sim-to-real performance gap bound.
6. Reinterpret OPM as a safety-preserving action-space constraint.

This would make the paper stronger theoretically, experimentally, and practically.
