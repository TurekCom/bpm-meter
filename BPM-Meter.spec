from importlib.metadata import distributions
from pathlib import Path

licenses = [
    (str(package.locate_file(file)), str(Path("licenses", file.parent)))
    for package in distributions()
    for file in (package.files or ())
    if any(part.endswith(".dist-info") for part in file.parts)
    and ("licenses" in file.parts or file.name.startswith(("LICENSE", "COPYING", "NOTICE")))
]

app = Analysis(
    ["bpm_meter.pyw"],
    datas=[*licenses, ("THIRD_PARTY_NOTICES.txt", ".")],
    excludes=["tkinter", "matplotlib"],
)

exe = EXE(
    PYZ(app.pure), app.scripts, app.binaries, app.datas,
    name="BPM-Meter", console=False, upx=False,
)
