# Idempotency and Retry

| Operation | Key / uniqueness boundary | Retry result | Expiry |
|---|---|---|---|
| Attempt start | optional client request key + attempt no/policy | same Attempt if semantic retry | bounded/request policy |
| Answer save | `client_change_id` within Attempt | original accepted/stale result | retained with answer-event policy |
| Attempt submit | idempotency key + one logical result/Attempt | same AssessmentResult | at least through terminal result lifetime |
| Regrade item | correction/job + Attempt unique | already-completed item observed | job/history retention |
| Notification fan-out | event + recipient + channel | no duplicate logical notification | event retention |
| Email delivery | notification/event + recipient + channel | continue same delivery attempts | delivery retention |
| File scan/process | FileRevision + scanner/processor version/job | same safe/rejected state | job lifecycle |
| Import job/item promotion | ImportJob/item identity | same promoted Question/result | import retention |
| RAG indexing/activation | KnowledgeVersion identity | same active/failed version state | knowledge retention |
| Backup/restore operation | operation UUID | do not repeat completed destructive action | operational retention |

A reused idempotency key with a materially different payload is a conflict, not a silent replay.
