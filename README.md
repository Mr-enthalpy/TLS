# tls_c1 Python wrapper handoff

This is a Codex handoff skeleton for wrapping the Zolix spectrometer SDK as a Python package.

Immediate target:

```python
from tls_c1 import tls_c1

spec = tls_c1()
spec.connect(Mono="Omni", port_type="USB", serial_number="OM319069")
spec.set_grating(1)
spec.set_wavelength("546 nm")
spec.move()
spec.disconnect()
```

Read `AGENTS.md` before implementation. The vendor SDK header `SDK/inc/spectrometer.h` is the ABI source of truth.

Default tests do not require hardware:

```bash
py -3.12 -m pytest
```

Hardware smoke tests are opt-in and will move the monochromator:

```bash
$env:TLS_C1_RUN_HARDWARE_TESTS = "1"
$env:TLS_C1_SERIAL = "OM319069"
$env:TLS_C1_SAFE_GRATING = "1"
$env:TLS_C1_SAFE_WAVELENGTH_NM = "546"
py -3.12 -m pytest tests\test_hardware_smoke.py -s
```
