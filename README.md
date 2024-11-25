# akimboxr

Hunter's reimplementation of the TapXR mapper, for use with dual-wielded tap devices.

This is not quite ready for use currently. Some simple stuff (immedate taps) work fine, but because I want to avoid some
of the issues that backspacing can cause with things like Vim, I've opted to build a threading approach that's not quite
there yet.

Contributions are welcome. The code is not currently licensed; feel free to use it at your own risk for personal use,
and contact me for commercial inquiries.

## Features
- [ ] Tapping
    - [x] Immediate taps (taps that only have one binding)
    - [ ] Deferred taps (multiple tap disambiguation)
    - [ ] Macros
    - [x] Pushing and Popping Layers
- [ ] Configuration
    - [x] Custom Layers
    - [x] Layers across devices (shift on one tap shifts on the other)
    - [x] Intercept Layers (i.e., press shift than do the lower layers)
- [ ] Advanced Tapping
  - [ ] Multi-device chords
  - [ ] Combos
  - [ ] Stenography Mode