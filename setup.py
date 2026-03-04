from setuptools import setup, find_packages

setup(
    name="eks-addons-cdk",
    version="1.0.0",
    description="Production-ready AWS CDK project for EKS cluster with addons and applications",
    author="Your Organization",
    url="https://github.com/your-org/eks-addons-and-apps-with-cdk",
    packages=find_packages(exclude=["tests*"]),
    install_requires=[
        "aws-cdk-lib==2.170.0",
        "constructs>=10.0.0,<11.0.0",
        "cdk-ecr-deployment==3.0.33",
        "cdk-sops-secrets==1.2.31",
        "aws-cdk-lambda-layer-kubectl-v32",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
