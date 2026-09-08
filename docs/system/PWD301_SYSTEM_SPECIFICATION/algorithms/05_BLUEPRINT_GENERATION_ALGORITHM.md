# Blueprint Generation Algorithm

Each rule specifies lesson/topic/difficulty/type/count. Query only active/eligible Question candidates for the Assessment Course, exclude forbidden duplicates where policy dictates, validate mandatory overlap, then compute shortage per rule. Publish is blocked with explicit shortage report if any rule cannot be met. Generation may materialize a pool; actual Attempt selection still freezes exact snapshot.
