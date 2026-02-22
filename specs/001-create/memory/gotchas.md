# Gotchas & Pitfalls

Things to watch out for in this codebase.

## [2026-01-31 22:25]
npm commands are blocked in this auto-claude environment. Database migrations (npm run prisma:migrate -- --name init) must be run externally after verifying PostgreSQL is running and the emenum database exists.

_Context: subtask-2-6 database migration_

## [2026-02-01 03:14]
npm, npx, node, and vitest commands are blocked in the auto-claude environment. Test execution (npm test -- --coverage) must be run externally. Test infrastructure verification can be done by reading test files and config.

_Context: subtask-17-2 unit test verification - commands blocked so verification done via file inspection_
