# oto-commit

`oto-commit` is a command-line tool that reads your staged git changes and asks Google Gemini to write a professional commit message that follows the [Conventional Commits](https://www.conventionalcommits.org/) specification.

## Installation

    pip install oto-commit

Or straight from GitHub:

    pip install git+https://github.com/ahmtsalih/oto-commit.git

Requires Python 3.8 or newer and `git` on your PATH.

## Setup

You need a Google Gemini API key (free at <https://aistudio.google.com/app/apikey>). Run:

    oto-commit setup

The key is requested with hidden input and stored in `~/.oto-commit-config.json`, readable only by your user account.

Alternatively, set the `GEMINI_API_KEY` environment variable; it takes precedence over the config file:

    # PowerShell
    $env:GEMINI_API_KEY = "your-key"

    # bash / zsh
    export GEMINI_API_KEY="your-key"

Avoid `oto-commit setup --api-key <key>`: the key would end up in your shell history.

## Usage

Stage your changes, then:

    git add .
    oto-commit generate

The tool prints a suggested commit message. Review it and use it with `git commit -m "..."`.

## What gets sent to Google

The **staged diff is sent to the Google Gemini API** to generate the message. Do not use this tool on repositories whose content you are not allowed to share with a third party. On the free tier Google may use submitted content to improve its products; check the current Gemini API terms before relying on it.

To reduce the risk of leaking secrets, `oto-commit`:

- **never sends** files that usually contain secrets, and lists them so you know they were skipped: `.env`, `.env.*`, `*.pem`, `*.key`, `*.p12`, `*.pfx`, `*.ppk`, `*.jks`, `*.keystore`, `id_rsa`, `id_dsa`, `id_ecdsa`, `id_ed25519`
- **scans the remaining diff** for things that look like API keys, tokens, private keys or password assignments, and asks for confirmation before sending
- sends your API key in a request header rather than the URL, stores it with `0600` permissions, and prints model output as plain text so a malicious diff cannot inject terminal escape sequences or fake links

These checks are heuristics, not guarantees. Review what you stage.

## Development

    git clone https://github.com/ahmtsalih/oto-commit.git
    cd oto-commit
    pip install -e .
    pip install pytest
    python -m pytest

## License

MIT
