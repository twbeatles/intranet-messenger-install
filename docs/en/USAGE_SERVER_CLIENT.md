[Korean version](../ko/USAGE_SERVER_CLIENT.md)

# Server/Client Usage Guide

## Server EXE

File: `MessengerServer.exe`

### GUI mode

```powershell
.\MessengerServer.exe
```

- Opens the server management window.
- Supports system tray controls.

### CLI mode

```powershell
.\MessengerServer.exe --cli
```

- Runs in console server mode.
- Default port: `5000`

### Access URLs

- Same machine: `http://127.0.0.1:5000`
- Intranet: `http://<server-ip>:5000`

## Client EXE

File: `MessengerClient.exe`

### Default run

```powershell
.\MessengerClient.exe
```

Default server URL: `http://127.0.0.1:5000`

### Run with explicit server URL

```powershell
.\MessengerClient.exe --server-url http://10.0.0.10:5000
```

### Runtime flow

1. starts in tray mode
2. attempts auto-login using stored device token
3. shows login window if restore fails
4. after login, provides rooms/messages/files/polls/admin features

## Operational Recommendations

- Server:
  - use static IP or DNS name
  - backup `messenger.db`, `uploads/`, `.secret_key`, `.security_salt`
- Client:
  - keep startup option on
  - publish first-run server URL policy to users

## Common Issues

- Auto-login restore fails:
  - verify server time sync
  - verify device session expiry/revocation
- File transfer fails:
  - verify `MAX_CONTENT_LENGTH`
  - verify upload token expiry
- Connection fails:
  - verify firewall/proxy WebSocket policy
