from setuptools import setup, find_packages

setup(
    name="envisaged",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.0.0",
        "click>=8.0.0",
    ],
    python_requires=">=3.7",
    entry_points={
        'console_scripts': [
            'gource-generator=envisaged.gource_generator.cli:main',
        ],
    },
)
