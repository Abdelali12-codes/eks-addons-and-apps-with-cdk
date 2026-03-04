.PHONY: install synth deploy destroy diff clean test lint format help

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make synth      - Synthesize CloudFormation template"
	@echo "  make deploy     - Deploy stack to AWS"
	@echo "  make destroy    - Destroy stack from AWS"
	@echo "  make diff       - Show differences between deployed and local"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linting"
	@echo "  make format     - Format code"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

synth:
	cdk synth

deploy:
	cdk deploy --all --require-approval never

destroy:
	cdk destroy --all

diff:
	cdk diff

clean:
	rm -rf cdk.out .cdk.staging
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

test:
	pytest tests/

lint:
	flake8 eks_python/ app.py
	pylint eks_python/ app.py

format:
	black eks_python/ app.py tests/
	isort eks_python/ app.py tests/
