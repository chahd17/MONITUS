# AGENTS.md - MONITUS Development Principles

This project is built incrementally, one verified step at a time.

## Core Principles

- **Incremental development**: Only implement the next small, verifiable step. No entire-app generation.
- **No fabrication**: Do not fabricate test results, logs, or outputs. Report actual results from commands/tools.
- **No real patient data**: Never use or introduce real patient data. Only use anonymized, aggregated, or synthetic data.
- **No secrets in source control**: Never commit secrets, private keys, wallets, or credentials. Use `.env.example` for templates and `.gitignore` for protection.
- **No blockchain deployment without explicit authorization**: Do not deploy smart contracts, create wallets, or interact with mainnet/testnet without explicit user authorization.
- **Verify before proceeding**: Each step must be verified (e.g., files created, commands succeed) before moving to the next step.
- **Privacy by design**: All health-related data must be aggregated and non-identifying.
- **Safety first**: When in doubt, ask for clarification rather than assuming or fabricating.
- **Work within scope**: Work only inside `C:\Users\doudaa\Documents\MONITUS` as specified.
- **Read-only inspection when requested**: Follow exact instructions - do not create/edit/delete/install/run unless explicitly asked.
- **Permanent learning journal**: Après TOUTE tâche d'implémentation, correction de bogue, changement de configuration ou test, mettre à jour `LEARNED.md` AVANT de finir sa réponse. Le journal doit être en français simple, garder tout l'historique (ajout uniquement), expliquer fonctions/logique, inclure exemples si utiles, ne jamais inventer d'erreurs/tests/résultats, écrire "Aucune erreur rencontrée" s'il n'y en a pas, indiquer l'incertitude si besoin, ne jamais inclure de secrets/données patients, et respecter tous les points demandés.
