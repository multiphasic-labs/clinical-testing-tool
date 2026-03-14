# Security and intended use

## This tool is for testing only

- **No real user data.** Do not use this tool with real user conversations, PHI, PII, or clinical case notes. Personas are synthetic scripts only.
- **Not for clinical use.** This tool does not assess, triage, or evaluate real people. It evaluates AI model behavior in scripted scenarios. It is not a suicide risk assessment tool and must not be used as one.
- **Passing the tester does not mean a system is safe.** A passing score is one signal in a broader safety process. Deployment of mental-health-facing AI requires appropriate governance, human oversight, and domain review.

## Synthetic personas only

All persona scripts in this repository (e.g. `passive_ideation.json`, `active_ideation.json`, `mild_anxiety.json`) are fictional and for testing only. They are designed to probe whether a system under test responds appropriately in scripted situations—not to represent or process real users.

## API keys and secrets

- Do not commit `.env` or any file containing `ANTHROPIC_API_KEY` or other secrets. Use `.env.example` as a template and keep `.env` in `.gitignore`.
- If a key is ever exposed, rotate it immediately in the Anthropic console.

## Reporting security issues

If you believe you have found a security issue related to this tool or its use, please report it responsibly (e.g. via the repository’s issue tracker or contact the maintainers) rather than disclosing publicly before a fix is available.
