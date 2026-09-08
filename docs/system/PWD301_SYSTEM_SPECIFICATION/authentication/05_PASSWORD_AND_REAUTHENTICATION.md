# Password and Reauthentication

Passwords use a current adaptive password hash supported by the approved Python stack; exact cost is configuration. Change/reset rotates relevant auth credentials and revokes sessions/tokens according to policy. Sensitive Admin action requires fresh password re-auth proof; extremely sensitive action additionally requires exact confirmation phrase and mandatory reason. Re-auth proof is short-lived and scoped, not a reusable password substitute.
