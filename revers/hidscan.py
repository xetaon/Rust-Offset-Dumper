import ctypes, ctypes.wintypes as w, struct, sys

hid = ctypes.WinDLL("hid.dll")
setupapi = ctypes.WinDLL("setupapi.dll")
kernel32 = ctypes.WinDLL("kernel32.dll")

DIGCF_PRESENT = 0x2
DIGCF_DEVICEINTERFACE = 0x10
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

class GUID(ctypes.Structure):
    _fields_ = [("Data1", w.DWORD), ("Data2", w.WORD), ("Data3", w.WORD), ("Data4", ctypes.c_ubyte * 8)]

class SP_DEVICE_INTERFACE_DATA(ctypes.Structure):
    _fields_ = [("cbSize", w.DWORD), ("InterfaceClassGuid", GUID), ("Flags", w.DWORD), ("Reserved", ctypes.POINTER(w.ULONG))]

class SP_DEVINFO_DATA(ctypes.Structure):
    _fields_ = [("cbSize", w.DWORD), ("ClassGuid", GUID), ("DevInst", w.DWORD), ("Reserved", ctypes.POINTER(w.ULONG))]

class HIDD_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Size", w.ULONG), ("VendorID", w.USHORT), ("ProductID", w.USHORT), ("VersionNumber", w.USHORT)]

class HIDP_CAPS(ctypes.Structure):
    _fields_ = [("Usage", w.USHORT), ("UsagePage", w.USHORT), ("InputReportByteLength", w.USHORT),
                ("OutputReportByteLength", w.USHORT), ("FeatureReportByteLength", w.USHORT),
                ("Reserved", w.USHORT * 17), ("NumberLinkCollectionNodes", w.USHORT),
                ("NumberInputButtonCaps", w.USHORT), ("NumberInputValueCaps", w.USHORT),
                ("NumberInputDataIndices", w.USHORT), ("NumberOutputButtonCaps", w.USHORT),
                ("NumberOutputValueCaps", w.USHORT), ("NumberOutputDataIndices", w.USHORT),
                ("NumberFeatureButtonCaps", w.USHORT), ("NumberFeatureValueCaps", w.USHORT),
                ("NumberFeatureDataIndices", w.USHORT)]

# HID GUID 4d1e55b2-f16f-11cf-88cb-001111000030
hid_guid = GUID(0x4d1e55b2, 0xf16f, 0x11cf, (ctypes.c_ubyte * 8)(0x88, 0xcb, 0x00, 0x11, 0x11, 0x00, 0x00, 0x30))

setupapi.SetupDiGetClassDevsW.restype = ctypes.c_void_p
setupapi.SetupDiGetClassDevsW.argtypes = [ctypes.POINTER(GUID), w.LPCWSTR, w.HWND, w.DWORD]
setupapi.SetupDiEnumDeviceInterfaces.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.POINTER(GUID), w.DWORD, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA)]
setupapi.SetupDiGetDeviceInterfaceDetailW.argtypes = [ctypes.c_void_p, ctypes.POINTER(SP_DEVICE_INTERFACE_DATA), ctypes.c_void_p, w.DWORD, ctypes.POINTER(w.DWORD), ctypes.c_void_p]
setupapi.SetupDiDestroyDeviceInfoList.argtypes = [ctypes.c_void_p]

hdev = setupapi.SetupDiGetClassDevsW(ctypes.byref(hid_guid), None, None, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE)
idx = 0
results = []
while True:
    did = SP_DEVICE_INTERFACE_DATA()
    did.cbSize = ctypes.sizeof(did)
    if not setupapi.SetupDiEnumDeviceInterfaces(hdev, None, ctypes.byref(hid_guid), idx, ctypes.byref(did)):
        break
    idx += 1
    size = w.DWORD(0)
    setupapi.SetupDiGetDeviceInterfaceDetailW(hdev, ctypes.byref(did), None, 0, ctypes.byref(size), None)
    buf = ctypes.create_string_buffer(size.value)
    if not setupapi.SetupDiGetDeviceInterfaceDetailW(hdev, ctypes.byref(did), buf, size, ctypes.byref(size), None):
        continue
    path = ctypes.wstring_at(ctypes.addressof(buf) + 4)

    h = kernel32.CreateFileW(path, 0, 3, None, 3, 0, None)
    if h == INVALID_HANDLE_VALUE:
        continue

    attrs = HIDD_ATTRIBUTES()
    attrs.Size = ctypes.sizeof(attrs)
    hid.HidD_GetAttributes(h, ctypes.byref(attrs))

    pp = ctypes.c_void_p()
    if not hid.HidD_GetPreparsedData(h, ctypes.byref(pp)):
        kernel32.CloseHandle(h); continue
    caps = HIDP_CAPS()
    hid.HidP_GetCaps(pp, ctypes.byref(caps))

    # product string
    prod = ctypes.create_unicode_buffer(256)
    hid.HidD_GetProductString(h, prod, 512)
    man = ctypes.create_unicode_buffer(256)
    hid.HidD_GetManufacturerString(h, man, 512)
    ser = ctypes.create_unicode_buffer(256)
    hid.HidD_GetSerialNumberString(h, ser, 512)

    # report descriptor via IOCTL
    IOCTL_HID_GET_REPORT_DESCRIPTOR = 0x000B0000
    rd = ctypes.create_string_buffer(4096)
    ret = w.DWORD(0)
    ok = kernel32.DeviceIoControl(h, IOCTL_HID_GET_REPORT_DESCRIPTOR, None, 0, rd, 4096, ctypes.byref(ret), None)
    desc = rd.raw[:ret.value] if ok else b""

    hid.HidD_FreePreparsedData(pp)
    kernel32.CloseHandle(h)

    results.append((attrs.VendorID, attrs.ProductID, prod.value, man.value, ser.value,
                    caps.UsagePage, caps.Usage, caps.InputReportByteLength,
                    caps.OutputReportByteLength, caps.FeatureReportByteLength, desc, path))

setupapi.SetupDiDestroyDeviceInfoList(hdev)

for (vid, pid, prod, man, ser, up, us, inl, outl, featl, desc, path) in results:
    if vid not in (0x0C45, 0x2EA8, 0x0D8C):
        continue
    print("=" * 80)
    print(f"VID_{vid:04X}&PID_{pid:04X}  usagePage=0x{up:04X} usage=0x{us:04X}")
    print(f"  product={prod!r} manuf={man!r} serial={ser!r}")
    print(f"  in={inl} out={outl} feature={featl} descLen={len(desc)}")
    print(f"  path={path}")
    print("  desc=" + desc.hex())
