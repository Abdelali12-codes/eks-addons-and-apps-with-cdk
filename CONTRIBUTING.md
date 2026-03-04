# Contributing Guidelines

## Getting Started

1. Fork the repository
2. Clone your fork
3. Create a feature branch
4. Make your changes
5. Submit a pull request

## Development Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks (optional)
pre-commit install
```

## Code Style

- Follow PEP 8 guidelines
- Use type hints where applicable
- Write docstrings for functions and classes
- Keep functions small and focused

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=eks_python tests/

# Run specific test
pytest tests/unit/test_eks_python_stack.py
```

## Linting and Formatting

```bash
# Format code
black eks_python/ app.py tests/
isort eks_python/ app.py tests/

# Lint code
flake8 eks_python/ app.py
pylint eks_python/ app.py
```

## Commit Messages

Follow conventional commits:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `refactor:` Code refactoring
- `test:` Test changes
- `chore:` Build/tooling changes

Example: `feat: add karpenter addon support`

## Pull Request Process

1. Update documentation if needed
2. Add tests for new features
3. Ensure all tests pass
4. Update CHANGELOG.md
5. Request review from maintainers

## Code Review

- Be respectful and constructive
- Focus on code quality and maintainability
- Suggest improvements, don't demand changes
- Approve when satisfied

## Questions?

Open an issue for discussion before major changes.
