# Vendor DLL placement

For local/internal use, copy DLLs from the uploaded SDK:

- `SDK/x64/spectrometer_x64.dll` -> `vendor/win_amd64/spectrometer_x64.dll`
- `SDK/x64/ftd2xx.dll` -> `vendor/win_amd64/ftd2xx.dll`
- `SDK/x86/spectrometer_x86.dll` -> `vendor/win32/spectrometer_x86.dll`
- `SDK/x86/ftd2xx.dll` -> `vendor/win32/ftd2xx.dll`

Do not publish vendor DLLs unless redistribution rights are confirmed.
