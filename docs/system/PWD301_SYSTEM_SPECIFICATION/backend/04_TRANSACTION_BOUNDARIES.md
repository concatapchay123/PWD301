# Transaction Boundaries

Transactions protect enroll capacity, role/suspension revocation, email activation, lesson reorder, question revision activation, assessment publish/start snapshot, lease acquire/save/submit, manual grade/history, correction/job creation, file revision activation, RAG version activation and sensitive audit. External calls occur outside DB transaction using persisted job/outbox state unless atomicity requires only local metadata.
