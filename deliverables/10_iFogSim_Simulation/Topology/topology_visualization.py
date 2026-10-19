"""Generate the topology diagram documented from the experiment source."""

from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    Image = ImageDraw = ImageFont = None


ROOT = Path(__file__).parent


def svg():
    return '''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="520" viewBox="0 0 1200 520">
  <rect width="1200" height="520" fill="#f7f8fa"/>
  <text x="600" y="42" text-anchor="middle" font-family="Arial" font-size="25" font-weight="bold" fill="#18212b">Implemented iFogSim prototype topology</text>
  <text x="600" y="72" text-anchor="middle" font-family="Arial" font-size="15" fill="#506070">Python service is a control-plane subprocess, not a simulated FogDevice</text>
  <line x1="260" y1="235" x2="600" y2="235" stroke="#506070" stroke-width="4"/>
  <line x1="600" y1="235" x2="940" y2="235" stroke="#506070" stroke-width="4"/>
  <text x="430" y="213" text-anchor="middle" font-family="Arial" font-size="15" fill="#303b46">parent link: 2 ms local uplink</text>
  <text x="770" y="213" text-anchor="middle" font-family="Arial" font-size="15" fill="#303b46">parent link: 45 ms edge uplink</text>
  <rect x="100" y="155" width="320" height="160" rx="12" fill="#dceeff" stroke="#2d6a9f" stroke-width="3"/>
  <rect x="440" y="155" width="320" height="160" rx="12" fill="#e3f4e8" stroke="#3b8651" stroke-width="3"/>
  <rect x="780" y="155" width="320" height="160" rx="12" fill="#fff0d5" stroke="#b87920" stroke-width="3"/>
  <text x="260" y="197" text-anchor="middle" font-family="Arial" font-size="23" font-weight="bold" fill="#18212b">Local</text>
  <text x="600" y="197" text-anchor="middle" font-family="Arial" font-size="23" font-weight="bold" fill="#18212b">Edge</text>
  <text x="940" y="197" text-anchor="middle" font-family="Arial" font-size="23" font-weight="bold" fill="#18212b">Cloud</text>
  <text x="260" y="232" text-anchor="middle" font-family="Arial" font-size="16" fill="#303b46">device: local</text>
  <text x="600" y="232" text-anchor="middle" font-family="Arial" font-size="16" fill="#303b46">device: edge</text>
  <text x="940" y="232" text-anchor="middle" font-family="Arial" font-size="16" fill="#303b46">device: cloud</text>
  <text x="260" y="267" text-anchor="middle" font-family="Arial" font-size="15" fill="#303b46">local_executor module</text>
  <text x="600" y="267" text-anchor="middle" font-family="Arial" font-size="15" fill="#303b46">edge_executor module</text>
  <text x="940" y="267" text-anchor="middle" font-family="Arial" font-size="15" fill="#303b46">cloud_executor module</text>
  <text x="260" y="295" text-anchor="middle" font-family="Arial" font-size="14" fill="#506070">Local route: 0 counted link bytes</text>
  <text x="600" y="295" text-anchor="middle" font-family="Arial" font-size="14" fill="#506070">Edge route: 12,000 up + 2,000 down</text>
  <text x="940" y="295" text-anchor="middle" font-family="Arial" font-size="14" fill="#506070">Cloud route: 2 hops, up/down</text>
  <rect x="255" y="390" width="690" height="72" rx="10" fill="#ffffff" stroke="#6c7782" stroke-width="2"/>
  <text x="600" y="420" text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" fill="#18212b">Python JSONL RL service</text>
  <text x="600" y="445" text-anchor="middle" font-family="Arial" font-size="14" fill="#506070">observation → action → outcome; runs outside simulated topology</text>
  <line x1="600" y1="390" x2="600" y2="315" stroke="#7a4d9e" stroke-width="3" stroke-dasharray="8,7"/>
</svg>'''


def main():
    (ROOT / "topology.svg").write_text(svg(), encoding="utf-8")
    if Image is not None:
        image = Image.new("RGB", (1200, 520), "#f7f8fa")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        draw.text((30, 30), "Implemented iFogSim prototype topology", fill="#18212b", font=font)
        boxes = [(100, 155, 420, 315, "Local\nlocal_executor"),
                 (440, 155, 760, 315, "Edge\nedge_executor"),
                 (780, 155, 1100, 315, "Cloud\ncloud_executor")]
        for left, top, right, bottom, label in boxes:
            draw.rounded_rectangle((left, top, right, bottom), radius=12, outline="#506070", width=3, fill="#ffffff")
            draw.multiline_text((left + 120, top + 65), label, fill="#18212b", anchor="mm", align="center", font=font)
        draw.line((420, 235, 440, 235), fill="#506070", width=4)
        draw.line((760, 235, 780, 235), fill="#506070", width=4)
        draw.text((100, 390), "Python JSONL service: control plane outside the simulated FogDevice topology", fill="#18212b", font=font)
        image.save(ROOT / "topology.png")
        print("wrote topology.svg and topology.png")
    else:
        print("wrote topology.svg; Pillow unavailable, PNG not generated")


if __name__ == "__main__":
    main()