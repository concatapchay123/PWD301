# User Account Workflows

Registration: validate/normalize unique email → hash password → create User+STUDENT role → optional verification/notification. Login: generic lookup/verify → active check → rotate session/create grant. Email change: pending token → verify new address → atomic activation. Suspension: reauth Admin → confirm/reason → revoke session/JWT → audit → notify. Deactivation/anonymization preserves required history.
