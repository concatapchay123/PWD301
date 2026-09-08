# Service Layer Rules

Services accept authenticated actor/context, load real resources, authorize object relationship, validate state, execute the smallest DB transaction, write required audit in the same transaction when failure must block, persist domain/outbox/job records, then return DTOs. Never trust role, score, progress, correct-answer flags, ownership or state supplied by client.
