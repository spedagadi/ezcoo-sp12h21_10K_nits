# SP12H21 — Dolby Vision LLDV target at the 10K (v2 max) setting

EZCOO **EZ-SP12H21** (4K120 HDMI 2.1 1×2 splitter) firmware with the Dolby
Vision VSVDB target raised to the maximum the EDID format can express.

Based on the official **`EZ-SP12H21_Ver1.09(DB13).hex`** (EZCOO, 30 Sep 2024).

## What changed

The Dolby VSVDB payload in all **six v2 EDID slots** (and the raw template
string):

```
before: 45 0b 90 86 60 76 8f
after:  45 0b f8 86 60 76 8f
```

| field | before | after |
|---|---|---|
| version | 2 | 2 |
| DM | 3.x | 3.x |
| interface | Low-Latency (LLDV) | Low-Latency (LLDV) |
| YUV 4:2:2 12-bit | yes | yes |
| target min | PQ 20 = 0.00063665 cd/m² | same |
| **target max** | PQ 3225 = **1387.41 cd/m²** | **PQ 4070 = 9434.03 cd/m²** |
| primaries | P3-D65 | P3-D65 |

- **9434 nits is the maximum of the v2 field** (max-luminance index 31, PQ 4070).
  The literal PQ maximum 4095 = 10000 nits needs a v0 block, which this EDID
  format does not use. For "the player should not tone-map", this is the top of
  the scale.
- The **v1 EDID slot** (a different lever mode, 350 nits) is untouched.
- Primaries remain **P3-D65**. A BT.2020 variant is possible but not included
  (payload `45 0b f8 57 98 a9 53` for DM 3.x, or `49 0b f8 57 98 a9 53` for DM 4.x).

## Folder

```
firmware/
  EZ-SP12H21_Ver1.09_ML9434.hex        <- flash this (10K / 9434 nits)
  EZ-SP12H21_Ver1.09(DB13).hex         <- stock restore
tools/
  gd32/GD32 All In One Programmer/     <- official GD32 programmer v5.4.0.42035
  drivers/win64/GD32DfuDrivers.exe     <- install this first (x64)
  drivers/win32/GD32DfuDrivers.exe     <- x86 machines
docs/
  SP12H21FRIMWAREUPDATE.zip            <- official EZCOO package
  GD MCU Programmer update guide.docx
  EX11PRO&SP12H2&SP12H21 update guide.mp4
verify/
  decode_edid.py                       <- read an EDID and print the VSVDB
  edid_parse.py                        <- general EDID/CEA block dump
  parse_fw.py                          <- find and decode EDIDs in a .hex
  patch_fw.py                          <- reproduce the patch from the stock hex
  sample_splitter_edid_after_flash.bin <- captured post-flash EDID (expected VSVDB)
SHA256SUMS.txt
```

## Flash (tested on this unit)

1. Run `tools/drivers/win64/GD32DfuDrivers.exe` and install the DFU driver.
2. Run `tools/gd32/GD32 All In One Programmer/GD32AllInOneProgrammer.exe`
   (self-contained; no Qt install needed).
3. Put the splitter in update mode: **hold the hidden UPDATE button and power it
   on**. The blue LED must blink about once per second.
4. Select Interface **USB**, BootLoader **DFU**, click **Connect**.
   The device is `GD32 Device in DFU Mode` (VID_28E9 / PID_0189).
5. In **Download**, click **Browse** and choose
   `firmware/EZ-SP12H21_Ver1.09_ML9434.hex`.
   If the file dialog filters `.bin`, change it to `.hex` / All files.
6. Tick **Verify after download**. Click **Download** and wait for **100% Finish**.
7. Disconnect, power-cycle the splitter (without holding UPDATE) to boot the app.

## Do not

- **Do not press Erase with "Full chip erase".** That erases the DFU bootloader at
  `0x08000000–0x08003FFF`. The application starts at `0x08004000`. `Download`
  with "Necessary erase" only erases the pages it writes.
- Do not flash SP12H2 firmware on the SP12H21.
- Do not unplug power or USB while the write is in progress.
- The part number may auto-detect as `GD32E103CBT6`; the C103 and E103 flash maps
  are identical (128 KB, 1 KB pages), so that is safe. `GD32C103CBT6` is the
  vendor tool's selection.

## Verify after flashing

With any HDMI source (PC GPU, laptop) on the splitter's input, dump the EDID the
splitter presents (`edid-decode` on Linux, or the registry EDID on Windows), then:

```
python verify/decode_edid.py splitter_edid.bin
```

Expected:

```
payload:     45 0b f8 86 60 76 8f
version:     2
DM:          3.x
interface:   Low-Latency
target min:  PQ 20 = 0.00063665 cd/m^2
target max:  PQ 4070 = 9434.03 cd/m^2
primaries:   P3-D65
```

On the CM3588 board, the VP shell logs the signal as
`vp: signal colorspace=10 xfer=120 quant=2 -> DV (BT.2020, no static metadata)`.

A captured post-flash EDID is included, so the decoder can be tested without
hardware:

```
python verify/decode_edid.py verify/sample_splitter_edid_after_flash.bin
```

## Restore

Same procedure with `firmware/EZ-SP12H21_Ver1.09(DB13).hex`.

## Notes

- The target max is stored as a 5-bit index in the v2 VSVDB; this firmware sets it
  to 31 (maximum). The exact value the player sees is **9434.03 cd/m²**, not 10000.
- Primaries are the stock P3-D65. If the downstream pipeline expects the player to
  leave BT.2020 untouched, a BT.2020 primaries variant is a second patch (not
  included here).
- Provenance: stock firmware from the EZCOO SP12H21 product page
  (`SP12H21FRIMWAREUPDATE.zip`, 30 Sep 2024); programmer from GigaDevice
  "GD32 All-In-One Programmer" v5.4.0.42035.
- This folder is self-contained: firmware, official programmer, driver, official
  documentation, and the verification/patch scripts.