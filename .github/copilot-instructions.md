- When chaining commands in the terminal, use a semicolon `;` as a separator. For example: `cd my-folder; git status`.

## Project Analysis

This is a Python-based password vault application with a graphical user interface.

- **Core Functionality**: The application allows users to store and manage passwords. It supports storing the password vault locally, or remotely on a user-controlled server via SSH. It also includes a steganography feature to hide the vault within a PNG image.
- **Technologies**:
    - **Backend**: Python
    - **GUI**: Tkinter (implied by the `.pyw` file extension and typical Python standard library usage)
    - **Cryptography**: `cryptography` library
    - **Remote Storage**: `paramiko` for SSH
    - **Steganography**: `pillow` for image manipulation
- **Project Structure**:
    - The main application logic is within the `acid_vault` directory.
    - `VaultGui.pyw` is the main entry point for the GUI application.
    - The core vault logic (encryption, data management) is likely in `acid_vault/vault/vault.py`.
    - Helper modules for features like SSH and steganography are in `acid_vault/vault/helpers/`.
    - The project includes tests in the `tests/` directory and dependencies are listed in `requirements.txt`.
- **Usage & Development**: Users typically run the application directly from the Git repository. To accommodate this and ensure production data is not used during development, the application will use a `dev_data` directory if a `.dev_sentinel` file is present at the root of the repository. This file is git-ignored. The AI assistant must check for the presence of the `.dev_sentinel` file at the start of any interaction. If the file is missing, the AI must warn the user that they might be in a production environment and that any changes could affect production data.

## Python Coding Guidelines

- Follow PEP8 style guide.
- Keep comments and docstrings to a maximum of 72 characters per line.
- Aim for a maximum of 80 characters per line for code, but allow up to 120 characters if it improves readability.

@import "./GIT_USAGE.md"

## Custom Commands

- `/save`: Saves the current work state (branch, uncommitted changes, conversation context, current goal, any other relevant information) to `resume_here.md`.
- `/resume`: Loads the work state from `resume_here.md` to continue a previous session.
