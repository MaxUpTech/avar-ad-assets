#!/usr/bin/env python3
"""Mix the music bed with voiceover lines (music ducks under the voice) and mux onto the silent reel.
usage: mix.py SILENT.mp4 MUSIC.wav OUT.mp4 [--sfx SFX.wav] [VO.wav@START ...]   e.g. line1.wav@0.1 line2.wav@1.9"""
import subprocess, sys
args = sys.argv[1:]
sfx = None
if "--sfx" in args:
    k = args.index("--sfx"); sfx = args[k + 1]; del args[k:k + 2]
silent, music, out, *vo = args
if sfx:  # pre-mix music + sound effects into one bed (SFX slightly on top)
    bed = out + ".bed.wav"
    subprocess.check_call(["ffmpeg", "-v", "error", "-y", "-i", music, "-i", sfx, "-filter_complex",
                           "[0:a]volume=0.8[m];[1:a]volume=1.0[s];[m][s]amix=inputs=2:normalize=0:duration=first[a]", "-map", "[a]", bed])
    music = bed
inputs = ["-i", silent, "-i", music]
chains, labels = [], []
for k, item in enumerate(vo):
    f, start = item.rsplit("@", 1)
    inputs += ["-i", f]
    ms = int(float(start) * 1000)
    chains.append(f"[{k+2}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={ms}|{ms}[v{k}]")
    labels.append(f"[v{k}]")
if vo:
    fc = ";".join(chains) + f";{''.join(labels)}amix=inputs={len(vo)}:normalize=0,apad[vo];" \
         "[vo]asplit[vo1][vo2];[1:a]aresample=48000[m];[m][vo1]sidechaincompress=threshold=0.03:ratio=8:attack=5:release=250[md];" \
         "[md][vo2]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1.0:LRA=9[a]"
else:
    fc = "[1:a]loudnorm=I=-14:TP=-1.0:LRA=9[a]"
subprocess.check_call(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "0:v", "-map", "[a]",
                       "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out])
print(out)
