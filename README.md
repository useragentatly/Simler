Simler v50.0 — Universal Lossless Compressor

Simler is a fast, universal lossless compressor designed for text, images, audio, PDFs, and binaries.
It supports multiple algorithms, integrity checks, streaming I/O, and can be used both from CLI and Python.

Key Features:

Algorithms: Huffman (word/phrase-aware), zlib, gzip, lzma

Integrity checks: sha256, crc32, or none

Streaming/chunked I/O for large files (memory-friendly)

CLI + Python API support

Phrase mode for better text compression

Multi-platform: works on desktops, servers, and edge devices

Suitable for storage savings, DB/AI pipelines, and large dataset handling



---

How to Use

Command Line

Compress a file:

python simler.py input_file output_file -a auto -l 6 --phrase --integrity sha256

Options:

input_file – file to compress

output_file – compressed output (.sim recommended)

-a / --algo – algorithm: auto, huffman, zlib, gzip, lzma

-l / --level – compression level 1–9

--phrase – enable Huffman phrase mode (text only)

--integrity – checksum: sha256, crc32, or none


Decompress a file:

python simler.py input_file.sim output_file --decompress

Automatically detects algorithm from metadata

Verifies integrity if SHA256 or CRC32 is used



---

Python API

from simler import Simler

# Initialize compressor
sim = Simler(algo="auto", level=6, integrity="sha256")

# Compress a file
sim.save_sim("data.txt", "data.sim", phrase_mode=True)

# Decompress a file
data = sim.load_sim("data.sim")

# Compression ratio
ratio = sim.get_compression_ratio("data.txt", "data.sim")
print(f"Compression ratio: {ratio:.2f}%")

API Parameters:

algo – compression algorithm

level – compression level (zlib/gzip/lzma)

phrase_mode – Huffman phrase mode for text

integrity – checksum type


Notes:

Huffman mode works best on UTF-8 text and may need sufficient RAM for dictionary building

Binary/non-text files default to zlib/lzma/gzip for reliability

Supports large file compression with minimal memory overhead
