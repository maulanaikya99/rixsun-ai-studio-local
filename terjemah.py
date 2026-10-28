#!/usr/bin/env python3
"""Ubah deskripsi bahasa Indonesia jadi prompt bahasa Inggris (otak pilihan, lihat otak.py). Usage: terjemah.py <gambar|video> "<teks>" """
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from otak import Otak

ATURAN = {
    "gambar": ("You write prompts for the FLUX image generator. Turn the user's description (often Indonesian) into ONE English "
               "prompt of 40-70 words: start with the art style (if none is given use 'cinematic photo' for real things or "
               "'3D animated film style' for cartoons), then subject, clothing/colors, setting, lighting, mood, camera. "
               "Never mention brands or studios. End with 'no text, no logo, no watermark'."),
    "video": ("You write prompts for the LTX image-to-video generator. The picture already exists; turn the user's description "
              "(often Indonesian) into ONE English prompt of 25-50 words describing only what MOVES: the characters' actions, "
              "nature (wind, water, light) and the camera movement. Present tense, no style words, no brands."),
}

mode, teks = sys.argv[1], " ".join(sys.argv[2:])
out = Otak().tanya(f"{ATURAN[mode]}\nReply with the prompt only.\n\nDescription: {teks}", max_tokens=160)
print(out.strip().strip('"').replace("\n", " "))
