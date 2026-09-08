# Enrollment Lifecycle

Enroll request → Course published/enrollable → capacity lock/check → prerequisite summary check → existing logical enrollment lookup → create/reactivate with new EnrollmentPeriod → initialize progress → success. Leave closes active period and starts 30-day retention. Rejoin creates new period/restarts progress. No rejoin >30 days allows detailed purge but keeps compact summary.
