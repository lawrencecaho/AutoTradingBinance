from setuptools import setup, find_packages

setup(
    name="autotradingbinance",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "python-multipart",
        "pyotp",
        "pydantic",
        "python-dotenv",
    ],
    python_requires=">=3.8",
)
