# Simler v4.5.0 — Universal Lossless Compressor

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)

Simler v4.5.0 is a high-performance, universal lossless compression tool. It supports text, images, audio, PDFs, and binary files with multiple algorithms and is designed for storage optimization, AI pipelines, databases, and mobile/edge devices.

---

## Features

- **Algorithms**: Huffman (phrase-aware for text), zlib, gzip, lzma  
- **Integrity Checks**: SHA256, CRC32, or None  
- **Streaming & Chunked I/O**: Memory-friendly for large files  
- **CLI & Python API**: Easy to integrate in scripts or applications  
- **Progress Callback**: For UI or monitoring integration  
- **Cross-Platform**: Works on servers, desktops, and mobile devices  

---

## Installation

```bash
git clone https://github.com/useragentatly/Simler-v4.5.0.git
cd Simler-v4.5.0
pip install -r requirements.txt
