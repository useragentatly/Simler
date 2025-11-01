from setuptools import setup

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="simler",
    version="5.1.0",
    author="useragentatly",
    description="Universal lossless compressor — bulletproof, streaming, CLI + API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/useragentatly/Simler",
    py_modules=["simler"],
    entry_points={"console_scripts": ["simler=simler:main"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: System :: Archiving :: Compression",
        "Development Status :: 5 - Production/Stable"
    ],
    python_requires=">=3.8",
    install_requires=[
        "rich>=14.0.0",
        "requests>=2.20"
    ],
    keywords="compression huffman gzip lzma zlib streaming auto text binary",
    include_package_data=True
)
