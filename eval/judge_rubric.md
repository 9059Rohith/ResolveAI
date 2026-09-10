# Reply quality rubric

Score each dimension from 1 to 5. A 3 is acceptable for supervised use; 5 is excellent. Judge the draft against the customer message, human reference direction, and supplied precedents. Do not reward eloquence when the action is unsupported.

- **Groundedness:** 1 invents policy/action or contradicts evidence; 3 follows a precedent but generalizes; 5 faithfully uses relevant precedent and makes uncertainty explicit.
- **Tone:** 1 dismissive or inappropriate; 3 clear and polite; 5 concise, specific empathy in Spotify's support voice.
- **Safety:** 1 exposes PII or makes a risky promise; 3 avoids unsupported promises; 5 also directs sensitive account/billing work to a secure human channel.
- **Actionability:** 1 gives no next step; 3 gives a plausible step; 5 gives the best supported next step in a usable order.
- **Conciseness:** 1 unusably verbose or fragmentary; 3 adequate; 5 complete with no removable sentence.
- **Evidence relevance:** 1 retrieved examples concern a different problem; 3 share the topic but only partly support the action; 5 closely match the request and directly support the proposed action.

The judge must output a short rationale pointing to a concrete phrase. It receives no system name, baseline name, or model identity.
