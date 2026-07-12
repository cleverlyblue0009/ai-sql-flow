# F1: Queries Requiring Both Gates (Joint-Required Cases)

**Definition**: a query is 'joint-required' if:
- SQL gate alone is WRONG (dirty+source ≠ true reference)
- Data gate alone is WRONG (clean+transpiled ≠ true reference)
- Joint gate is CORRECT (clean+source = true reference)

## Result: 0 joint-required queries

No queries were found where BOTH single gates fail but the joint gate succeeds.

**Interpretation**: within this query corpus, the joint gate does not provide additional error reduction beyond the better single gate.
