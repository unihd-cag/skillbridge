# Security Policy

## Supported Versions


| Version | Supported          |
| ------- | ------------------ |
| 1.5.x   | :white_check_mark: |
| < 1.5   | :x:                |

## Reporting a Vulnerability

At the moment there is no way to report a security vulnerability. Should you encounter one, please open an issue **only stating that you found a vulnerability**. We will figure something out then.

## Skillbridge Security

Skillbridge is a code translator between Cadence SKILL and Python. That means it is the very nature of skillbridge to run code on your behalf.
A malicious user with access to the machine running the skillbridge server can inject arbitrary code **that will be run**.

On linux, only the user that opened the Workspace has access to the connection. On windows, **everyone** on the same machine has access to the connection.

Note: If you change the default settings, the above restrictions may not apply.
