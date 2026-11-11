# Copilot Instructions

## Project Guidelines
- For cross-tool concepts such as EMME attribute domains, prefer a single shared C# enum over per-module string fields or nested duplicate enums.

## Testing Guidelines
- For EMME tool integration tests, derive from TestBase and invoke the module through Helper.Modeller; keep tests that specifically verify no EMME call isolated from TestBase initialization.