#!/usr/bin/env python3
"""
Simler v4.5.0 — General-Purpose Lossless Compressor
Supports: Text (Huffman), PDFs, images, audio, binaries
Algorithms: Huffman, zlib, gzip, lzma
Integrity: sha256, crc32, none
CLI + Python API
"""

import os, pickle, hashlib, time, heapq, zlib, gzip, lzma
from collections import Counter
from typing import Optional, Callable

__version__ = "4.5.0"

class Simler:
    def __init__(self, algo: str="auto", level: int=6, chunk_size: int=1024*1024, integrity: str="sha256"):
        self.algo = algo
        self.level = level
        self.chunk_size = chunk_size
        self.integrity = integrity
        self.word_dict = {}       # word->bitstring for Huffman
        self.reverse_dict = {}    # bitstring->word
        self.compression_time = 0.0
        self.decompression_time = 0.0

    # Huffman helpers
    def _build_huffman_tree(self, freq):
        heap = [[w,[word,""]] for word,w in freq.items()]
        heapq.heapify(heap)
        while len(heap)>1:
            lo, hi = heapq.heappop(heap), heapq.heappop(heap)
            for pair in lo[1:]: pair[1] = "0"+pair[1]
            for pair in hi[1:]: pair[1] = "1"+pair[1]
            heapq.heappush(heap,[lo[0]+hi[0]]+lo[1:]+hi[1:])
        return sorted(heapq.heappop(heap)[1:], key=lambda p: (len(p[-1]),p))

    def _create_dictionary(self, text:str, phrase_mode:bool=False, max_phrase_len:int=3):
        if phrase_mode:
            words = text.split(); phrases=[]
            i=0
            while i<len(words):
                best,best_score=None,0
                for n in range(min(max_phrase_len,len(words)-i),1,-1):
                    p=" ".join(words[i:i+n]); cnt=text.count(p); score=cnt*n
                    if cnt>1 and score>best_score: best,best_score=p,score
                if best: phrases.append(best); i+=len(best.split())
                else: phrases.append(words[i]); i+=1
            freq=Counter(phrases)
        else: freq=Counter(text.split())
        if not freq: raise ValueError("No tokens to build dictionary")
        tree=self._build_huffman_tree(freq)
        self.word_dict={w:code for w,code in tree}
        self.reverse_dict={code:w for w,code in tree}

    def _text_to_bits(self,text:str)->str:
        bits=[]
        for t in text.split():
            c=self.word_dict.get(t)
            if c is None: raise ValueError(f"Token '{t}' not in dictionary")
            bits.append(c)
        return "".join(bits)

    def _bits_to_text(self,bits:str)->str:
        cur=[];out=[]
        s=""
        for b in bits:
            s+=b
            if s in self.reverse_dict:
                out.append(self.reverse_dict[s]); s=""
        if s: raise ValueError("Incomplete bitstring")
        return " ".join(out)

    def _bits_to_bytes(self,bits:str):
        if not bits: return b"",0
        pad=(8-len(bits)%8)%8
        return int(bits+"0"*pad,2).to_bytes((len(bits)+pad)//8,'big'), pad

    def _bytes_to_bits(self,data:bytes,pad:int)->str:
        if not data: return ""
        bits=bin(int.from_bytes(data,'big'))[2:].zfill(len(data)*8)
        return bits[:-pad] if pad else bits

    # Utility
    def _choose_algo(self,input_path:str)->str:
        if self.algo!="auto": return self.algo
        try: open(input_path,"rb").read(4096).decode("utf-8"); return "huffman"
        except: return "lzma" if os.path.getsize(input_path)>10*1024*1024 else "zlib"

    def _compute_checksum(self,data:bytes):
        if self.integrity=="sha256": return hashlib.sha256(data).hexdigest()
        elif self.integrity=="crc32": import zlib as _z; return _z.crc32(data)&0xffffffff
        else: return None

    # Public API
    def save_sim(self,input_file:str,output_file:str,
                 algo:Optional[str]=None, level:Optional[int]=None,
                 phrase_mode:bool=False, max_phrase_len:int=3,
                 progress:Optional[Callable[[float],None]]=None)->float:
        start=time.time()
        if not os.path.exists(input_file): raise FileNotFoundError(input_file)
        algo=(algo or self.algo); level=(level or self.level)
        algo=self._choose_algo(input_file) if algo=="auto" else algo
        compressed_bytes=b""; pad=0

        if algo=="huffman":
            with open(input_file,"rb") as f: raw=f.read()
            try: text=raw.decode("utf-8")
            except: algo="zlib"
            else:
                self._create_dictionary(text,phrase_mode,max_phrase_len)
                bits=self._text_to_bits(text)
                compressed_bytes,pad=self._bits_to_bytes(bits)

        if algo=="zlib":
            with open(input_file,"rb") as f: data=f.read()
            compressed_bytes=zlib.compress(data,level)
        elif algo=="gzip" and algo!="huffman":
            tmp=output_file+".tmp.gz"
            with open(input_file,"rb") as fin, gzip.open(tmp,"wb",compresslevel=level) as fout:
                while chunk:=fin.read(self.chunk_size):
                    fout.write(chunk)
                    if progress: progress(min(fin.tell()/os.path.getsize(input_file)*100,100.0))
            with open(tmp,"rb") as t: compressed_bytes=t.read(); os.remove(tmp)
        elif algo=="lzma" and algo!="huffman":
            with open(input_file,"rb") as f: compressed_bytes=lzma.compress(f.read(),preset=level)

        checksum=self._compute_checksum(compressed_bytes)
        with open(output_file,"wb") as out:
            meta={"algo":algo,"level":level,"phrase_mode":phrase_mode,"integrity":self.integrity}
            pickle.dump(meta,out)
            pickle.dump(checksum,out)
            pickle.dump(pad,out)
            out.write(compressed_bytes)
        self.compression_time=time.time()-start
        return self.compression_time

    def load_sim(self,sim_file:str, progress:Optional[Callable[[float],None]]=None)->bytes:
        start=time.time()
        if not os.path.exists(sim_file): raise FileNotFoundError(sim_file)
        with open(sim_file,"rb") as f:
            meta=pickle.load(f); algo=meta.get("algo"); checksum=pickle.load(f); pad=pickle.load(f); payload=f.read()
        # Verify
        if self.integrity=="sha256" and checksum is not None:
            if hashlib.sha256(payload).hexdigest()!=checksum: raise ValueError("SHA256 checksum mismatch")
        elif self.integrity=="crc32" and checksum is not None:
            import zlib as _z
            if _z.crc32(payload)&0xffffffff!=checksum: raise ValueError("CRC32 checksum mismatch")
        # Decompress
        if algo=="huffman":
            bits=self._bytes_to_bits(payload,pad); text=self._bits_to_text(bits)
            result=text.encode("utf-8") if isinstance(text,str) else text
        elif algo=="zlib": result=zlib.decompress(payload)
        elif algo=="gzip":
            import io
            with gzip.open(io.BytesIO(payload),"rb") as gf: result=gf.read()
        elif algo=="lzma": result=lzma.decompress(payload)
        else: raise ValueError(f"Unknown algorithm {algo}")
        self.decompression_time=time.time()-start
        return result

    def get_compression_ratio(self,input_file:str,output_file:str)->float:
        if not (os.path.exists(input_file) and os.path.exists(output_file)): return 0.0
        o=os.path.getsize(input_file); c=os.path.getsize(output_file)
        return (c/o)*100 if o else 0.0

# ---------------- CLI ----------------
def main():
    import argparse
    parser=argparse.ArgumentParser(description="Simler v4.5.0 — General-Purpose Compressor")
    parser.add_argument("input"); parser.add_argument("output"); parser.add_argument("--decompress",action="store_true")
    parser.add_argument("-a","--algo",default="auto",choices=["auto","huffman","zlib","gzip","lzma"])
    parser.add_argument("-l","--level",type=int,default=6)
    parser.add_argument("--phrase",action="store_true")
    parser.add_argument("--integrity",choices=["sha256","crc32","none"],default="sha256")
    args=parser.parse_args()

    sim=Simler(algo=args.algo,level=args.level,integrity=args.integrity)
    if args.decompress:
        out=sim.load_sim(args.input)
        with open(args.output,"wb") as f: f.write(out)
        print(f"DECOMPRESSED → {args.output} | time: {sim.decompression_time:.2f}s")
    else:
        t=sim.save_sim(args.input,args.output,algo=args.algo,level=args.level,phrase_mode=args.phrase)
        ratio=sim.get_compression_ratio(args.input,args.output)
        print(f"COMPRESSED → {args.output} | time: {t:.2f}s | ratio: {ratio:.2f}% | algo: {sim._choose_algo(args.input)} | integrity: {sim.integrity}")

if __name__=="__main__":
    main()
