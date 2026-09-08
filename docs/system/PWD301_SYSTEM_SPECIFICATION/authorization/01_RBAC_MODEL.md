# RBAC Model

Roles are cumulative capability markers, not complete authorization. Allowed role sets are exactly STUDENT; STUDENT+INSTRUCTOR; STUDENT+INSTRUCTOR+ADMIN. Service logic rejects invalid partial combinations. Ownership/enrollment/course relationship is checked after role evaluation. Role changes are audited/notified and never create a new User.
