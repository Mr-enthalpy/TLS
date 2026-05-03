from tls_c1.api import SpectrometerAPI

api = SpectrometerAPI()
print("DLL:", api.get_dll_ver())
count = api.enum_dev_count()
print("devices:", count)
for i in range(count):
    print(i, api.enum_dev_sn(i))
