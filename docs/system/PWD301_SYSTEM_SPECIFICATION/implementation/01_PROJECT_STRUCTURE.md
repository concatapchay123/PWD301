# Project Structure

**DERIVED IMPLEMENTATION DESIGN** if repository does not already have an equivalent structure; existing repo conventions take precedence.

```text
app/
  auth/ users/ courses/ learning/ questions/ assessments/ attempts/ grading/
  files/ imports/ ai/ notifications/ admin/ api/
  services/ policies/ workers/ templates/ static/
migrations/
tests/
instance-or-private-storage/
```

Prefer reuse of existing modules/dependencies. Do not create duplicate service/repository abstractions when current code already supplies the responsibility.
