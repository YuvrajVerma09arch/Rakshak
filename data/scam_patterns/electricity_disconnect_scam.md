# Pattern: Electricity-bill disconnect threat

**Kill chain:** hook=utility bill → pressure=disconnect tonight/today → trust_abuse=impersonates
electricity board officer → action=pay to personal VPA or call "officer" → rail=UPI push
**Anchor:** State DISCOMs bill on fixed cycles and never demand instant UPI payment to a
personal VPA; disconnection needs written notice.

Typical messages:
- "Dear consumer your electricity power will be disconnected tonight 9:30 pm because your previous month bill was not updated. Immediately contact officer 98xxxxxx"
- "Bijli bill baki hai, aaj raat connection kat jayega. Turant ₹200 bharo."

Tell-tales: personal mobile number as "officer"; night-time deadline; personal VPA; no consumer
number referenced in message.

Ambiguity note: genuine bill reminders exist — this pattern is MEDIUM confidence on text alone;
recipient reputation and payment history decide.
