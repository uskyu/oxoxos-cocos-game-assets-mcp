# Security Policy

## Supported versions

Security fixes are applied to the latest tagged minor release. Until the first public release, use the current default branch only for evaluation.

## Reporting a vulnerability

Use GitHub private vulnerability reporting after the public repository is enabled. Do not open a public issue containing a token, private path, exploit details, or user data. Before publication, contact the repository owner through a private channel and add that channel here.

Include the affected version, operating system, MCP client, reproduction steps, and impact. Remove all secrets from logs.

## Token exposure

If an OXOXOS token may have been exposed:

1. revoke it immediately at https://api.oxoxos.com/console/token;
2. create a replacement;
3. remove it from files, logs, CI variables, and shell history;
4. if committed, clean Git history and assume every clone still contains it;
5. review API usage at https://api.oxoxos.com/console.

Deleting a token from the newest commit does not invalidate the exposed credential.

## Security model

This MCP runs with the permissions of the local user and can read user-selected images and write to user-selected output directories. Configure the client with least privilege. The repository never needs administrator/root access.

- Keep tokens out of source, prompts, command arguments, and stdout.
- Review paths before granting access to sensitive directories.
- Pin released package versions for production use.
- Review dependency and release provenance before installing updates.
- Treat model output and remote URLs as untrusted data.
