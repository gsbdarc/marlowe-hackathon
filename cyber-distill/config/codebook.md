<!-- codebook_v1: copy of the README Codebook section. Any change after Stage 7 starts means relabeling; bump to codebook_v2 and log it. -->

# Codebook v1

Each paragraph gets one label, no more. The models score the answer letter.

| Letter | Label | Definition |
|---|---|---|
| A | NONE | Not about cybersecurity. |
| B | RISK | Cyber threats described as possible future harm to the company. |
| C | GOVERNANCE | How the company manages cyber risk: security leadership, board or committee oversight, frameworks such as NIST, audits, training, insurance, incident response plans. |
| D | INCIDENT | A specific cybersecurity incident that happened to the company, or to a vendor in a way that affected the company. It gives at least one concrete detail: when it happened, the system or data affected, a consequence, or the response. |
| E | PRODUCT | Cybersecurity products or services the company sells, or the market for them. |

If a paragraph fits more than one label, choose in this order: INCIDENT, GOVERNANCE, RISK, PRODUCT, NONE.

**Edge cases**

| Example text | Label | Rule |
|---|---|---|
| We have experienced cyberattacks in the past, none of which were material. | RISK | No specific incident. |
| In March 2025, a breach at our payroll vendor exposed employee Social Security numbers, and we notified affected employees. | INCIDENT | Vendor incident that affected the company. |
| A breach of the financial covenants in our credit agreement could result in an event of default. | NONE | Contract or covenant breach. |
| The virus and related restrictions reduced store traffic during 2020. | NONE | Disease. |
| We have completed Year 2000 readiness testing of our computer systems. | NONE | Date-handling problem with no attacker. |
| A global IT outage caused by a faulty software update disrupted our operations. | NONE | No malicious actor. DARC decision; revisit after the hand check. |
| We are subject to privacy laws such as the GDPR and the CCPA. | NONE | Privacy compliance with no security content. |
| Privacy laws require us to notify customers if their data is breached. | RISK | Security content present. |
| We maintain cyber liability insurance. | GOVERNANCE | Insurance is risk management. |
| A security software company describing a breach of its own systems | INCIDENT | Label what happened, not what the company sells. |

Any codebook change after Stage 7 starts means relabeling. Bump the version (`codebook_v2`, `prompt_v2.txt`) and log the change.
