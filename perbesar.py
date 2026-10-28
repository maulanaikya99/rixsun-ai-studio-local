#!/usr/bin/env python3
"""Perbesar gambar 2x dengan Real-ESRGAN x2plus (GPU M4). Usage: perbesar.py <gambar...>  -> <nama>_2x.png di sebelahnya."""
import os, subprocess, sys, time
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image

AI = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # folder AI (portabel)
ESR = f"{AI}/models/realesrgan/RealESRGAN_x2plus.pth"
DEV = "mps" if torch.backends.mps.is_available() else "cpu"

class RDB(nn.Module):
    def __init__(self, nf=64, gc=32):
        super().__init__()
        self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
        self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
        self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
        self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
        self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        x1 = self.lrelu(self.conv1(x))
        x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
        x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
        x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
        return self.conv5(torch.cat((x, x1, x2, x3, x4), 1)) * 0.2 + x


class RRDB(nn.Module):
    def __init__(self, nf, gc=32):
        super().__init__()
        self.rdb1, self.rdb2, self.rdb3 = RDB(nf, gc), RDB(nf, gc), RDB(nf, gc)

    def forward(self, x):
        return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x


class RRDBNetX2(nn.Module):
    """Real-ESRGAN generator, scale 2 (pixel-unshuffled input)."""

    def __init__(self, nf=64, nb=23, gc=32):
        super().__init__()
        self.conv_first = nn.Conv2d(12, nf, 3, 1, 1)
        self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
        self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
        self.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
        self.lrelu = nn.LeakyReLU(0.2, True)

    def forward(self, x):
        feat = self.conv_first(F.pixel_unshuffle(x, 2))
        feat = feat + self.conv_body(self.body(feat))
        feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
        feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
        return self.conv_last(self.lrelu(self.conv_hr(feat)))


def upscale(model, img, tile=256, ov=16):
    x = torch.from_numpy(img).permute(2, 0, 1).float().div(255)[None].to(DEV).half()
    h0, w0 = x.shape[2:]
    x = F.pad(x.float(), (0, w0 % 2, 0, h0 % 2), mode="replicate").half()   # pixel_unshuffle butuh ukuran genap
    _, _, h, w = x.shape
    out = torch.zeros(1, 3, h * 2, w * 2, device=DEV, dtype=torch.half)
    for y0 in range(0, h, tile):
        for x0 in range(0, w, tile):
            ya, xa, yb, xb = max(0, y0 - ov), max(0, x0 - ov), min(h, y0 + tile + ov), min(w, x0 + tile + ov)
            with torch.no_grad():
                o = model(x[:, :, ya:yb, xa:xb])
            hh, ww = (min(h, y0 + tile) - y0) * 2, (min(w, x0 + tile) - x0) * 2
            oy, ox = (y0 - ya) * 2, (x0 - xa) * 2
            out[:, :, y0 * 2:y0 * 2 + hh, x0 * 2:x0 * 2 + ww] = o[:, :, oy:oy + hh, ox:ox + ww]
    out = out[:, :, :h0 * 2, :w0 * 2]
    return (out.float().clamp(0, 1)[0].permute(1, 2, 0).cpu().numpy() * 255 + 0.5).astype(np.uint8)


if __name__ == "__main__":
    sd = torch.load(ESR, map_location="cpu", weights_only=True)
    sd = sd.get("params_ema", sd.get("params", sd))
    esr = RRDBNetX2()
    esr.load_state_dict(sd, strict=True)
    esr = esr.eval().to(DEV).half()
    for path in sys.argv[1:]:
        t = time.time()
        img = Image.open(path)
        alpha = img.getchannel("A") if img.mode in ("RGBA", "LA") else None
        hd = upscale(esr, np.array(img.convert("RGB")))
        out = Image.fromarray(hd)
        if alpha is not None:
            out.putalpha(alpha.resize(out.size, Image.LANCZOS))
        dst = os.path.splitext(path)[0] + "_2x.png"
        out.save(dst)
        print(f"  {os.path.basename(path)}: {img.width}x{img.height} -> {out.width}x{out.height}  ({time.time() - t:.1f} dtk)", flush=True)
        if not os.environ.get("NO_OPEN"): subprocess.run(["open", dst])
