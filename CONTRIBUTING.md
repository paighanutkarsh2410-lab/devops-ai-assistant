# Contributing

Thank you for your interest in contributing to the AI-Powered DevOps Assistant!

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/devops-ai-assistant.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Follow the [Developer Guide](docs/DEVELOPER.md) for local setup

## Development Workflow

1. Make your changes
2. Write tests for new features
3. Run tests: `cd agents && py -3.12 -m pytest tests/ -v`
4. Run backend tests: `cd backend && py -3.12 -m pytest tests/ -v`
5. Commit with a clear message
6. Push to your fork
7. Open a Pull Request

## Code Style

### Python
- Follow PEP 8
- Use type hints on public functions
- Keep functions under 50 lines
- Write docstrings for public classes and methods

### TypeScript
- Follow ESLint configuration
- Use `'use client'` directive for client components
- Use TypeScript interfaces for props

## Pull Request Process

1. **Title**: Clear, concise description of the change
2. **Description**: What changed and why
3. **Tests**: Include tests for new features
4. **Docs**: Update documentation if needed
5. **No breaking changes** without discussion

## Reporting Issues

Use GitHub Issues with the appropriate template:
- **Bug Report**: Include steps to reproduce, expected vs actual behavior
- **Feature Request**: Describe the use case and proposed solution

## Questions?

Open a GitHub Discussion or reach out via issues.
