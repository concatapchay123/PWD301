# Form Validation

Flask-WTF performs CSRF and server validation for web forms. Client validation is usability only. Normalize email/course code/title where uniqueness applies; validate dates/ranges/types/files; revalidate state/authorization at transaction time. Field errors map to stable codes/messages without exposing sensitive internals. PRG is used for normal HTML form submissions where appropriate.
