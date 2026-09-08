# IDOR Prevention

- Use opaque public UUID/GUID identifiers externally; this reduces guessability but is not authorization.
- For every object endpoint, resolve object then enforce actor-object relationship.
- Never expose sequential internal IDs as authorization evidence.
- Nested endpoints verify parent-child consistency (Question belongs Course, Attempt belongs Assessment, File reference belongs authorized resource).
- Return 404 vs 403 consistently to avoid protected-resource enumeration where appropriate.
- Add negative integration tests using valid IDs from another Student/Instructor/Course.
