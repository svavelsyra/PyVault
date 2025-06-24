## Git Usage Guidelines

- Explicitly add each file to git instead of using `git add .`.

## Git Commit Message Guidelines

This project follows the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification.

The commit message should be structured as follows:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**

The following types are most commonly used:

*   **feat**: A new feature
*   **fix**: A bug fix
*   **docs**: Documentation only changes
*   **style**: Changes that do not affect the meaning of the code (white-space, formatting, missing semi-colons, etc)
*   **refactor**: A code change that neither fixes a bug nor adds a feature
*   **perf**: A code change that improves performance
*   **test**: Adding missing tests or correcting existing tests
*   **build**: Changes that affect the build system or external dependencies
*   **ci**: Changes to our CI configuration files and scripts
*   **chore**: Other changes that don't modify src or test files

**Example:**

```
feat(ssh): add support for public key authentication

Adds the ability to connect to an SSH server using a public key instead of a password.
```
