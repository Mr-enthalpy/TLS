from tls_c1 import tls_c1

spec = tls_c1()
try:
    spec.connect(Mono="Omni", port_type="USB", serial_number="OM319069")
    spec.set_grating(1)
    spec.set_wavelength("546 nm")
    spec.move()
finally:
    spec.disconnect()
