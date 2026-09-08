# Lesson Completion Algorithm

Exact thresholds were not locked; use **CONFIGURABLE DEFAULTS**, not hardcoded business truth.

Inputs: bounded accumulated active-view seconds, content-view evidence ratio/sections, Lesson type, prior completion. Ignore implausible client deltas and duplicate activity IDs. Completion becomes true only when both configured minimum meaningful time and viewed-most threshold pass. Once completed, ordinary reorder/material rewrite does not clear completion. Server stores evidence summary and `completed_at`.
