# File Deduplication

Stream upload to quarantine while computing SHA-256 and size; validate size/type before expensive parsing. Find/create `file_blobs` by content hash with uniqueness race handling. Create logical FileAsset/FileRevision referencing blob. Dedup never bypasses per-revision security state: logical revision must still satisfy policy/scanner provenance before activation. Physical bytes delete only when no logical revision references remain and recovery/history policy permits.
