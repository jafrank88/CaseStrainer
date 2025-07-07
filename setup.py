from setuptools import setup, find_packages

setup(
    name="casestrainer",
    version="0.5.7",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "flask",
        "flask-session",
        "flask-cors",
        "requests",
        "beautifulsoup4",
        "python-dotenv",
        "eyecite",
        "waitress",
        "concurrent-log-handler",
        "python-dateutil",
        "pytest",
        "pytest-cov",
    ],
    python_requires=">=3.7",
)
