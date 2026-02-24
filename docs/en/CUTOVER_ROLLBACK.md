[Korean version](../ko/CUTOVER_ROLLBACK.md)

# Cutover and Rollback Plan

## Cutover Strategy

1. Server-first deployment
- deploy version with `device_sessions` schema/API
- allow both web and desktop access (`DESKTOP_ONLY_MODE=False`)

2. Pilot rollout
- distribute `MessengerClient.msi` to limited users
- validate startup/auto-login/reconnect scenarios

3. Organization-wide rollout
- enforce minimum client version (`DESKTOP_CLIENT_MIN_VERSION`)
- publish download URL

4. Desktop-only switch
- set `DESKTOP_ONLY_MODE=True`
- web root shows desktop migration notice

## Go/No-Go Gates

- 100% pass on core feature checklist
- security regression tests pass
- pilot incident rate is within threshold
- rollback rehearsal is complete

## Transition Considerations

1. UX
- internal DNS/certificate distribution strategy
- first-run server URL entry UX
- forced update timing (work hours vs off-hours)

2. Operations
- SQLite single-file backup/lock strategy
- mitigation for server single point of failure
- log collection and incident ticket integration

3. Security/Compliance
- device session expiry/revocation policy
- local token storage policy (Windows account scope)
- file retention/deletion policy

4. Release
- MSI code-signing required
- channel split (stable/canary)
- auto-update phase-2 introduction (phase-1 is check API)

## Rollback Scenario

1. Server rollback
- restore previous server binary/package
- immediately switch `DESKTOP_ONLY_MODE=False`

2. Client rollback
- redeploy previous `MessengerClient.msi`
- lower minimum-version policy

3. Data compatibility
- `device_sessions` is additive schema only
- no impact on existing room/message/user data

## Operational Commands

```powershell
# Desktop-only mode
.\scripts\set_cutover_mode.ps1 -Mode desktop-only -MinVersion 1.0.0 -LatestVersion 1.0.0

# Hybrid mode (for rollback)
.\scripts\set_cutover_mode.ps1 -Mode hybrid -MinVersion 1.0.0 -LatestVersion 1.0.0
```
