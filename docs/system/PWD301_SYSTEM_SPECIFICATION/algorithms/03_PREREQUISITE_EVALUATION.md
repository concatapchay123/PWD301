# Prerequisite Evaluation

For every direct prerequisite of target Course, load durable `course_completion_summaries` for Student. All required prerequisites must be satisfied. Prior completion continues to count after re-enrollment. Course prerequisite graph mutation runs cycle detection (DFS/topological reachability): adding A→B is rejected if B already reaches A. Archive/delete is blocked while active Course depends on it.
