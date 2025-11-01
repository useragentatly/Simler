#!/usr/bin/env python3
import os, sys, pickle, hashlib, zlib, lzma, time, argparse
from concurrent.futures import ThreadPoolExecutor, as_completed

class Simler:
    def __init__(self, chunk_size=1024*1024, integrity='sha256', verbose=False, max_workers=4):
        self.chunk_size = chunk_size
        self.integrity = integrity
        self.verbose = verbose
        self.compression_time = 0.0
        self.decompression_time = 0.0
        self.compression_ratio = 0.0
        self.decompression_ratio = 0.0
        self.max_workers = max_workers

    def log(self, msg):
        if self.verbose:
            print(f"[SIMLER] {msg}", file=sys.stderr)

    def _checksum(self, data: bytes):
        if self.integrity=='none' or not data:
            return None
        return hashlib.sha256(data).hexdigest()

    def _choose_algo(self, path, size):
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.txt','.csv','.log','.json','.xml']:
            return 'zlib'
        if ext in ['.png','.jpg','.jpeg','.bmp','.gif']:
            return 'zlib'
        if ext in ['.mp3','.wav','.ogg','.mp4','.avi','.mkv']:
            return 'lzma'
        if size > 50*1024*1024:
            return 'lzma'
        return 'zlib'

    def _compress_file(self, path):
        original_size = os.path.getsize(path)
        algo = self._choose_algo(path, original_size)
        compressed_data = b''
        with open(path,'rb') as f:
            while chunk := f.read(self.chunk_size):
                if algo == 'zlib':
                    compressed_data += zlib.compress(chunk)
                elif algo == 'lzma':
                    compressed_data += lzma.compress(chunk)
                else:
                    compressed_data += zlib.compress(chunk)
        checksum = self._checksum(compressed_data)
        compressed_size = len(compressed_data)
        ratio = compressed_size / original_size if original_size else 0
        return (path, compressed_data, checksum, compressed_size, original_size, ratio, algo)

    def create_archive(self, inputs, output_file):
        start = time.time()
        archive = {}
        seen_hashes = {}
        total_original = 0
        total_compressed = 0
        file_list = []

        for path in inputs:
            if os.path.isfile(path):
                file_list.append(path)
            elif os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for f in files:
                        file_list.append(os.path.join(root,f))

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self._compress_file, f): f for f in file_list}
            for future in as_completed(futures):
                path, data, chksum, c_size, o_size, ratio, algo = future.result()
                total_original += o_size
                total_compressed += c_size
                versioned = archive.get(path, {})
                if chksum in seen_hashes:
                    versioned['duplicate_of'] = seen_hashes[chksum]
                else:
                    versioned['data'] = data
                    versioned['size'] = c_size
                    versioned['checksum'] = chksum
                    versioned['algo'] = algo
                    seen_hashes[chksum] = path
                versioned.setdefault('versions', []).append({'timestamp': time.time(), 'checksum': chksum})
                versioned['compression_ratio'] = ratio*100
                archive[path] = versioned

        with open(output_file,'wb') as out:
            pickle.dump(archive,out)
        self.compression_time = time.time()-start
        self.compression_ratio = (total_compressed/total_original)*100 if total_original else 0
        return output_file

    def extract_archive(self, archive_file, output_dir, preview=False):
        start = time.time()
        total_original = 0
        total_extracted = 0
        with open(archive_file,'rb') as f:
            archive = pickle.load(f)
        for path, info in archive.items():
            rel_path = os.path.relpath(path)
            out_path = os.path.join(output_dir, rel_path)
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            if 'data' in info:
                data = info['data']
                total_original += info['size']
                total_extracted += len(data)
                info['decompression_ratio'] = (len(data)/info['size'])*100 if info['size'] else 0
                if preview and os.path.splitext(path)[1].lower() in ['.txt','.csv','.log','.json','.xml']:
                    snippet = data[:256].decode(errors='replace')
                    print(f"[Preview] {path}: {snippet}...")
                else:
                    with open(out_path,'wb') as fout:
                        fout.write(data)
        self.decompression_time = time.time()-start
        self.decompression_ratio = (total_extracted/total_original)*100 if total_original else 0

    def list_archive(self, archive_file):
        with open(archive_file,'rb') as f:
            archive = pickle.load(f)
        for path, info in archive.items():
            if 'data' in info:
                size = info['size']
                checksum = info['checksum']
                compression_ratio = info.get('compression_ratio',0)
                decompression_ratio = info.get('decompression_ratio',0)
                algo = info.get('algo','unknown')
            else:
                size = 0
                checksum = f"duplicate_of:{info['duplicate_of']}"
                compression_ratio = 0
                decompression_ratio = 0
                algo = 'duplicate'
            versions = len(info.get('versions',[]))
            print(f"{path} | {size} bytes | {checksum} | versions: {versions} | Algo={algo} | Compression={compression_ratio:.2f}% | Decompression={decompression_ratio:.2f}%")

    def delete_from_archive(self, archive_file, files_to_delete):
        with open(archive_file,'rb') as f:
            archive = pickle.load(f)
        for fdel in files_to_delete:
            if fdel in archive:
                del archive[fdel]
        with open(archive_file,'wb') as f:
            pickle.dump(archive,f)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--create", nargs="+")
    parser.add_argument("--extract")
    parser.add_argument("--list")
    parser.add_argument("--delete", nargs="+")
    parser.add_argument("-o","--output")
    parser.add_argument("--preview", action="store_true")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()

    sim = Simler(verbose=args.verbose, max_workers=args.workers)

    if args.create and args.output:
        sim.create_archive(args.create, args.output)
        print(f"Archive created → {args.output} | Time {sim.compression_time:.2f}s | Compression={sim.compression_ratio:.2f}%")
    elif args.extract and args.output:
        sim.extract_archive(args.extract, args.output, preview=args.preview)
        print(f"Archive extracted → {args.output} | Time {sim.decompression_time:.2f}s | Decompression={sim.decompression_ratio:.2f}%")
    elif args.list:
        sim.list_archive(args.list)
    elif args.delete and args.output:
        sim.delete_from_archive(args.output, args.delete)
    else:
        parser.print_help()

if __name__=="__main__":
    main()
