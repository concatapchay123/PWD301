# Regrading Workflow

Instructor edits used Question → classify answer-only vs content/choices → create new revision/correction + required audit → enqueue RegradeJob → worker enumerates retained eligible affected attempts → per-item recompute/full-credit → append grade/result histories → mark item → progress/resume on retry → notify Students whose score changed → job complete.
