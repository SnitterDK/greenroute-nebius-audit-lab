# Security

- Never commit API keys, .env files, account identifiers or private prompts.
- The live adapter sends only six allowlisted numeric estimate fields.
- Provider errors are replaced with a fixed local error message.
- Model output is advisory and always requires human review.
- If a credential is exposed, revoke it in Token Factory first.
