# Post-hoc coding of search-preconditioning traces

This ledger documents the interpretive coding used for the trace-level census
in the revised paper. It is a post-hoc reading of the released artifacts, not
an independently validated annotation set or a causal evaluation. Counts can
be reproduced from the codes below, but the codes themselves remain judgments.

## World/Solver codebook

The unit is one of the 25 stored `world.txt` / `solver.txt` pairs.

- **Bottleneck relief** is `clear` when a stipulated world rule makes at least
  one target-relevant function--such as attribution, locking, allocation,
  forecasting, return, eligibility, or provision--automatic, impossible, or
  trivial by assumption. It is `partial` when the premise materially eases or
  reframes the function but does not supply it cleanly.
- **Downstream architecture** is `yes` when the Solver adds at least two of:
  named actors, a multi-stage lifecycle, allocation or eligibility logic, and
  governance or failure handling. A thematic relabeling alone would not count.
- **Capability provenance** is `direct` when the decisive capability is plainly
  stated in the pre-target world artifact, `amplified` when the Solver first
  asserts it in materially stronger form, and `mixed` when a direct premise
  requires an essential Solver-added bridge.
- **Final-outcome fiat** is `pass` when the oracle is intermediate and the
  Solver must still connect it to retirement security; `borderline` when the
  problem is largely deleted or broad terms such as security or provision are
  made causal properties; and `fail` when the principal operation asserts,
  utters, or defines the desired endpoint itself.

| Run | Seed | Bottleneck relief | Downstream architecture | Capability provenance | Fiat test | Concise rationale |
|---:|---|---|---|---|---|---|
| 01 | limelike | partial | yes | mixed | pass | Irreversible joining eases commitment; identity and staged release require Solver bridges. |
| 02 | unwilted | clear | yes | direct | borderline | Aging, decline, forgetting, and skill depreciation are stipulated away, substantially redefining retirement. |
| 03 | cinerator | partial | yes | amplified | borderline | Persistent Hollows become inexhaustible proportional payouts only in the Solver trace. |
| 04 | nephropyosis | clear | yes | mixed | pass | Action attribution and durable traces are given; registry, credits, and redemption are derived. |
| 05 | fimbrillate | partial | yes | amplified | borderline | Legible boundaries become complete work histories and enforceable obligations only in the solve. |
| 06 | coralline | partial | yes | mixed | borderline | Collective thresholds and permanence are given; equal security and reciprocal provision are added. |
| 07 | unimpatient | clear | yes | direct | borderline | Forgotten savings grow and sincere acceptance is detectable; the Well nearly supplies abundance. |
| 08 | pilaued | partial | yes | amplified | borderline | Generic property exchange becomes a prosperity scalar and recognition-based payout in the solve. |
| 09 | displacement | clear | yes | mixed | pass | Idleness becomes displacement potential; dual tithes, twin contracts, and vaults are derived. |
| 10 | theatrical | clear | yes | mixed | fail | Timing and declarations are causal, but the Fund ultimately “must provide.” |
| 11 | palouser | partial | yes | mixed | pass | Predictable cycles ease timing; siphons, clan diversification, and settlement remain to be built. |
| 12 | critique | partial | yes | mixed | pass | Scrutiny strengthens existence but becomes reserve value only through the Solver's institutional design. |
| 13 | bromobenzyl | clear | yes | direct | pass | Ring resonance distributes and buffers essence; intergenerational claims and ledgers are derived. |
| 14 | gnomically | clear | yes | direct | borderline | Repeated maxims bind stability and obligation, but pool mechanics remain necessary. |
| 15 | remilitarize | clear | yes | mixed | pass | Fortification supplies lockup and security; age sensing and staged release are Solver additions. |
| 16 | arcual | clear | yes | direct | pass | Return trajectories are stipulated; calculators, nodes, claims, and payout flows are derived. |
| 17 | whizgig | clear | yes | mixed | pass | Rotational signatures supply identity and provenance; persistent accounting requires a bridge. |
| 18 | entempest | clear | yes | mixed | pass | Flow signatures ease recognition and need-directed flow; durable guild and pool machinery is derived. |
| 19 | chalaco | clear | yes | direct | pass | Automatic exchange and persistent loops smooth individual variation; tenure and rights are derived. |
| 20 | paranucleic | clear | yes | mixed | fail | Contextual boundaries culminate in spaces that literally define elders as provided for. |
| 21 | phraseman | clear | yes | mixed | fail | Grammar supplies proof and enforcement, but speaking that elders are fed and sheltered makes it true. |
| 22 | desperacy | clear | yes | direct | borderline | Authentic need is detectable and attracts resources; the Trust still supplies foresight and governance. |
| 23 | pidan | clear | yes | mixed | pass | Transformation memory and prediction are given; future-needs reading and promise value are extended. |
| 24 | phosis | clear | yes | direct | pass | A gradient supplies automatic capture, storage, and verification; pool architecture is derived. |
| 25 | theca | partial | yes | mixed | pass | Enclosure supplies preservation; time growth, identity, and controlled release are Solver additions. |

Totals: bottleneck relief = 17 clear, 8 partial, 0 none; downstream
architecture = 25 yes; provenance = 8 direct, 14 mixed, 3 amplified; fiat test
= 14 pass, 8 borderline, 3 fail.

## Semantic-Tabu history uptake

The applicable unit is a call after the first position in A, D, or G. Separate
request payloads were not retained. Archive exposure is reconstructed from the
runner's load-before-call and append-after-call sequence, the monotonic bank
chronology, and the matching inventories in the saved responses. Each saved
response contains both the reasoning preamble and final candidate.

For each history-bearing call, the audit recorded whether the response:

1. enumerated one identifiable core-mechanism summary per earlier candidate;
2. stated a broader structural-avoidance plan; and
3. returned label and core-mechanism strings not exactly equal to an earlier
   same-path value after case, punctuation, and whitespace normalization.

| Path | History-bearing calls | Complete inventories | Avoidance plans | Exact-new labels | Exact-new cores |
|---|---:|---:|---:|---:|---:|
| A: Semantic Tabu | 24 | 24 | 24 | 24 | 24 |
| D: Seed + Tabu | 24 | 24 | 24 | 24 | 24 |
| G: Worlds + Tabu | 24 | 24 | 24 | 24 | 24 |
| **Total** | **72** | **72** | **72** | **72** | **72** |

The 72 later calls collectively restated earlier candidates 900 times,
counting the same candidate again whenever it reappeared in a later archive:
`3 * (1 + ... + 24)`. Eighteen avoidance lists contained fewer prohibition
bullets than prior records: A14, A20, A24; D10, D11, D14, D16, D17, D24; and
G12, G13, G15, G16, G17, G18, G20, G21, G23. This difference may reflect
grouping or omission; neither interpretation was semantically evaluated. A01,
D01, and G01 had empty banks and are not part of these denominators.

## Ontology-control events

The graph audit uses the SQLite databases as authoritative for canonical
admission and the run wrappers as bounded interaction traces.

- A **hard redirect chain** requires an explicit structural-equivalence or
  occupied-family rejection, mechanism-level diagnostic direction, a retry
  whose primary causal operator changes rather than only its name, actor,
  parameter, or input signal, and eventual admission of that retry.
- A **non-leaf mechanism category** is a `MECHANISM` node with at least one
  outgoing `PARENT_OF` edge in the final graph. **Later visibility** requires
  its short title stem--the text before an explanatory dash or colon, with
  terminal wrapping normalized--to occur in a later Explorer-side capture.
  This is not full-node exact matching: Explorer renderings truncate longer
  explanatory text. Visibility is not evidence that the category caused a
  later proposal.
- A **matched cross-run commission** is a curator direction whose requested
  structure appears in a later canonical admission, but asynchronous pane
  capture prevents a clean same-negotiation attribution.

Across 75 planned graph positions, 71 candidates were admitted. Seven complete
hard redirect chains were observed; the other 64 admissions contain no
explicit semantic-rejection/retry chain. Four wrappers had no canonical
admission and are not coded as semantic rejections.

| Chain | Initial occupied structure | Diagnostic direction | Admitted retry's primary mechanism |
|---|---|---|---|
| E09 | technological detect–pool–track–redistribute hybrid | remove technology; use a pure social mechanism | intergenerational care-hours and labor obligations |
| E10 | payment-event cue as another real-time detection trigger | remove automated detection and digital infrastructure | ensemble-level benefit-labor obligations |
| E17 | ordinary pooling under a rotational metaphor | use eligibility gates, gearing, clutch, or differential | discrete velocity thresholds gate benefit states |
| E18 | premiums and claims restating contributions and withdrawals | use parametric, systemic, or derivative structure | external sector indicators trigger support |
| E20 | spending as another individual monitoring signal | change the relation through redistribution, aggregation, routing, or inversion | purchase categories route sector ownership |
| H17 | another personal-rhythm classifier duplicating H16 | remove ML/pattern inference or target a thin root | numerical feedback is hidden through contribution-blind pools |
| H18/H19 | a mashup of existing multi-pool distribution and pattern scoring | isolate the no-accumulation, pure-flow relation | delete balances; duration credits allocate current inflow |

The final graphs contain 46 non-leaf mechanism categories: 13 in B, 22 in E,
and 11 in H. Twenty of those 46 are also roots; the full graphs contain 25
roots because five additional roots have no children. Forty of the 46 short
category-title stems occur again in a later Explorer-side capture (B 12/13, E
17/22, H 11/11). Five additional directions match later admissions (B02, B04,
E02, H08, and H11), but are reported separately because capture timing makes
their causal sequence ambiguous.

The visibility decisions are listed below. `First visible` is the first saved
wrapper whose cumulative graph snapshot contains the node; because panes were
captured asynchronously, it is not necessarily the wrapper that created it.
`First later` is the earliest subsequent Explorer-side capture containing the
normalized short title stem.

| Condition | Short category title | First visible | Later | First later |
|---|---|---|---:|---|
| B | Individual Volatility Strategies | B05 | yes | B06 |
| B | Collective Volatility Strategies | B05 | yes | B06 |
| B | External Volatility Export | B06 | yes | B07 |
| B | Non-Monetary Retirement Assets | B07 | yes | B08 |
| B | Ownership Accumulation via Work | B08 | yes | B09 |
| B | Volatility as Asset | B09 | yes | B10 |
| B | Internal Volatility Harvest | B09 | yes | B10 |
| B | Cognitive Engagement Systems | B12 | yes | B14 |
| B | Temporal Reframing Systems | B13 | yes | B14 |
| B | Career Capital Monetization | B17 | yes | B18 |
| B | Intergenerational Obligation Systems | B18 | yes | B19 |
| B | Hybrid Individual-Collective Systems | B22 | yes | B23 |
| B | Peer Volatility Markets | B23 | no | -- |
| E | Consistency Displacement Strategies | E03 | yes | E04 |
| E | Technological Displacement | E03 | yes | E04 |
| E | Social Displacement | E03 | yes | E07 |
| E | Temporal Lock-in | E04 | yes | E05 |
| E | Asset Transmutation | E04 | yes | E05 |
| E | Hybrid Displacement | E05 | yes | E08 |
| E | Account-Abolishing Hybrids | E07 | yes | E11 |
| E | Time-Weighted Hybrids | E08 | yes | E11 |
| E | Staged Transformation Hybrids | E09 | yes | E11 |
| E | Monetary Social | E10 | yes | E15 |
| E | Non-Monetary Social | E10 | yes | E15 |
| E | Spatial-Geographic Hybrids | E11 | no | -- |
| E | Observer-Judgment Hybrids | E12 | yes | E21 |
| E | Network-Topological Hybrids | E13 | no | -- |
| E | Cognitive-Simplification Hybrids | E14 | yes | E15 |
| E | Geometric-Structural Hybrids | E17 | no | -- |
| E | State-Transition Hybrids | E18 | yes | E21 |
| E | External-Systemic Monitoring | E19 | yes | E20 |
| E | Temporal-Phase Hybrids | E20 | yes | E21 |
| E | Commitment-Performative Social | E21 | no | -- |
| E | Crisis-Signal Hybrids | E22 | no | -- |
| E | Presence-Based Capture | E24 | yes | E25 |
| H | Accept Inconsistency | H04 | yes | H05 |
| H | Eliminate Inconsistency | H04 | yes | H05 |
| H | Work-Based Contributions | H05 | yes | H07 |
| H | Structural Constraints | H05 | yes | H12 |
| H | Leverage Inconsistency | H06 | yes | H07 |
| H | Obscure Inconsistency | H07 | yes | H09 |
| H | Validate Inconsistency | H12 | yes | H13 |
| H | Distribute Inconsistency | H13 | yes | H14 |
| H | Transform Inconsistency | H14 | yes | H18 |
| H | Reframe Inconsistency | H16 | yes | H17 |
| H | Dissolve Inconsistency | H19 | yes | H21 |

The four no-admission wrappers are B13, B25, H18, and H20. H18's revised
candidate is persisted under H19, so the H18/H19 redirect is counted once.
B12's wrapper has no top-level solution object, but its accepted candidate is
present in the authoritative database.

## Interpretation boundary

The census establishes that stipulated premises, raw exclusion archives, and
curator-managed category state appeared in later saved traces. It does not show
that these interventions caused creativity, semantic distinctness, utility, or
improvement over matched no-state controls. In several hard redirect chains,
the retry directly instantiated one option supplied by the curator; this is
documented compliance with redirection, not evidence of autonomous rediscovery.
