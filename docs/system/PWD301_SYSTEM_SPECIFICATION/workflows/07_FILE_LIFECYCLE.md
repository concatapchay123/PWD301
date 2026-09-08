# File Lifecycle

Upload → metadata/size/type validation → quarantine → blob dedup → malware/resource checks → processing → SAFE revision → atomic activation/logical reference. Scan failure/unavailable remains blocked. Replacement creates a new revision; old active becomes recovery revision only after new passes. Deleted logical reference waits recovery and shared-blob reference checks before physical deletion.
