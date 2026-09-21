# Cross-Cutting Principles

Active principles across all skills and operations in PWD301.

## 1. Pure Headless API-First Invariant
Backend exclusively serves machine-readable, standardized JSON envelopes. Never attempt to mix server-rendered templates (Jinja) or static UI assets into backend blueprints. All client applications consume standardized REST or session endpoints.

## 2. Iron Law of Empirical Verification (Anti-Hallucination)
Never declare a task "DONE", "PASSED", or "FIXED" without actual empirical execution and verification in the current turn. Evidence before assertions always. Never fabricate test outputs, mock hardware telemetry, or bypass checks.

## 3. Fail-Closed Security by Default
Untrusted data, unverified files, pending antivirus scans, expired leases, or ambiguous permissions must fail closed. If the scanner, token, or permission check cannot verify safety, access is unconditionally denied.

## 4. Authentic System Reality vs Synthetic Simulation
System telemetry, resource monitoring, and performance counters must measure authentic physical hardware and operating system metrics (via `psutil` or native platform APIs). Synthetic, simulated, or calculated placeholders are prohibited in production monitoring.

## 5. Zero-Trust LLM Defense & Scope Bounding
Autonomous AI assistants ("Bạch tuộc AI") must be bounded by deterministic input filters and strict persona boundaries. The AI must never disclose internal credentials, database structure, or system topology, and must reject out-of-scope inquiries.

## 6. Ponytail Principle of Radical Simplicity ("Backend Complex, Frontend Simple")
"Backend có thể phức tạp. Frontend phải đơn giản." The best code and UI is that which does not need to be written. Avoid unneeded animations, redundant navigation, nested container cards, and speculative abstractions. User-facing simplicity always supersedes agent-invented complexity.
