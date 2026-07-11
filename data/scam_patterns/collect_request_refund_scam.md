# Pattern: Fake refund via UPI collect request

**Kill chain:** hook="you are owed a refund/cashback" → action=accept collect request or enter
UPI PIN "to receive" → rail=UPI collect
**Anchor:** NPCI: entering your UPI PIN or accepting a collect request SENDS money — you never
need a PIN to RECEIVE money. This single fact defeats the whole pattern.

Typical flow: marketplace "buyer" or "support agent" sends a collect request titled "refund";
victim approves and enters PIN, money leaves the account.

Tell-tales: collect request from unknown VPA; "enter PIN to receive"; support agent contacted
via a number found on a fake helpline listing.

Safe step: reject collect requests from unknown VPAs; receiving money never needs a PIN.
