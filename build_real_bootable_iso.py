from io import BytesIO
import os
import pycdlib

# Paths
ISO_ROOT = 'iso_root'
OUTPUT_ISO = 'output_bootable.iso'
BOOT_IMG = r'C:\Users\divin\Downloads\winpe_boot.img'  # change if needed

iso = pycdlib.PyCdlib()
iso.new(joliet=1, vol_ident='EXE2ISO')

# --- 1. Create /FILES directory (no ;1 for directories) ---
iso.add_directory('/FILES', joliet_path='/FILES')

# --- 2. Add autorun.inf at root ---
autorun_path = os.path.join(ISO_ROOT, 'autorun.inf')
with open(autorun_path, 'rb') as f:
    autorun_data = f.read()

iso.add_fp(
    BytesIO(autorun_data),
    len(autorun_data),
    iso_path='/AUTORUN.INF;1',
    joliet_path='/autorun.inf'
)

# --- 3. Add FILES/test.txt explicitly ---
test_path = os.path.join(ISO_ROOT, 'FILES', 'test.txt')
with open(test_path, 'rb') as f:
    test_data = f.read()

iso.add_fp(
    BytesIO(test_data),
    len(test_data),
    iso_path='/FILES/TEST.TXT;1',
    joliet_path='/FILES/test.txt'
)

# --- 4. Add boot image as BOOT.IMG and mark as El Torito ---
with open(BOOT_IMG, 'rb') as f:
    boot_data = f.read()

iso.add_fp(
    BytesIO(boot_data),
    len(boot_data),
    iso_path='/BOOT.IMG;1',
    joliet_path='/BOOT.IMG'
)

# The magic fix: keep boot_load_size small so it fits in 16-bit
iso.add_eltorito('/BOOT.IMG;1', boot_load_size=4)

# --- 5. Write ISO ---
iso.write(OUTPUT_ISO)
iso.close()

print('✅ Bootable ISO created:', OUTPUT_ISO)
