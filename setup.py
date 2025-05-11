from setuptools import setup, find_packages

setup(
    name="kademlia_dpos",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "kademlia>=2.2.2",
        "Flask>=2.0.1",
        "requests>=2.26.0",
        "cryptography>=37.0.4",
        "aiohttp>=3.8.1",
        "asyncio>=3.4.3",
        "pycryptodome>=3.14.1"
    ],
    entry_points={
        'console_scripts': [
            'kademlia-dpos-server=kademlia_dpos.api:main',
            'kademlia-dpos-cli=kademlia_dpos.cli:main',
        ],
    },
    author="Your Name",
    author_email="your.email@example.com",
    description="A Kademlia-based DPoS voting system",
    keywords="blockchain, dpos, kademlia, p2p, voting",
    url="https://github.com/yourusername/kademlia_dpos",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires=">=3.8",
) 