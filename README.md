# bifrost-agent-setup

Automatically set up your coding agents and LLM clients from Bifrost model catalog

## Usage

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Download this program
git clone https://github.com/m13253/bifrost-agent-setup.git
cd bifrost-agent-setup

# Edit config.json
cp config.example.json config.json
${EDITOR:-nano} config.json

# Run bifrost-agent-setup
./bifrost-agent-setup omp pi vscode zed
```

## Can you support other coding agents?

Sure, send me a Feature Request, or better, a Pull Request.

## Why isn’t there Claude Code or Codex?

They are supported by Bifrost officially: https://docs.getbifrost.ai/cli-agents/overview

## Disclaimer

This project is not affiliated with Bifrost.
