from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="simler",
    version="4.5.0",
    author="useragentatly",
    description="Universal lossless compressor — auto-detects text/binary",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/useragentatly/Simler-v4.5.0",
    py_modules=["simler"],
    entry_points={
        "console_scripts": ["simler=simler:main"]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Archiving :: Compression",
        "Development Status :: 5 - Production/Stable"
    ],
    python_requires=">=3.8",
    keywords="compression huffman gzip lzma zlib text binary streaming auto",
)
