# labels_to_gds.py
# Requires: pip install gdsfactory
import gdsfactory as gf
import os

# Target folder
OUT_DIR = r"C:\Users\shai\OneDrive\Micralyne 2025\Production 2025\GDS Files\Temporary pads"

COORDS = (13, -60)   # center position (x, y)
FONT_SIZE = 175     # adjust if needed
LAYER = (1, 0)       # GDS layer

def make_label(text: str, out_dir: str):
    c = gf.Component(f"{text}_label")
    txt = gf.components.text(text=text, size=FONT_SIZE, layer=LAYER)
    ref = c.add_ref(txt)
    ref.center = COORDS
    filename = os.path.join(out_dir, f"{text} label.gds")
    c.write_gds(filename)
    print(f"[SAVED] {filename}")
    return c

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    labels = ["AG1", "AG2", "AG3", "AG4","AG5", "L1", "L2", "M1", "M2","X","A"]
    for lbl in labels:
        make_label(lbl, OUT_DIR)

if __name__ == "__main__":
    main()
