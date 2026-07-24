# Clean pixel-art fixture provenance

`examples/inputs/clean-pixel-art.png` is an original, programmatically authored
in-repository test fixture. It depicts a simple blue cat face; no third-party
artwork or user attachment was used.

The source pattern is a 16 × 16 logical pixel grid, rasterized with nearest-
neighbor scaling to a 64 × 64 RGBA PNG. Its seven RGBA colors are:

- transparent `(255, 255, 255, 0)`
- outline `(34, 43, 65, 255)`
- blue `(72, 164, 236, 255)`
- light blue `(153, 217, 255, 255)`
- navy `(43, 88, 156, 255)`
- white `(255, 255, 255, 255)`
- pink `(245, 130, 150, 255)`

It was added after the task controller resolved the brief's missing public
pixel-art input by approving a local Pillow-authored fixture.
