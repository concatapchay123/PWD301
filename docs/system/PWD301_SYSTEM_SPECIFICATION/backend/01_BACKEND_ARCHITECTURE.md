# Backend Architecture

Use Flask application factory + Blueprints/modules, SQLAlchemy models, explicit policy/service layer and background workers. Routes parse/authenticate then call services. Services own state transitions, transaction boundaries and audit/event creation. Repositories/query helpers implement pagination/filter/index-aware access. External adapters isolate storage, ClamAV, Gemini and email.
