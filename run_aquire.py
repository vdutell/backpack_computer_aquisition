import ximea_cam_aquire_save as xim
import run_analysis as ana
import numpy as np

max_frames=20000
ipf = 100

xim.ximea_acquire("./test", max_frames=max_frames, ims_per_file=ipf)

od_dfp = ana.count_missed_frames('./test/timestamps_od.tsv', 'od')
os_dfp = ana.count_missed_frames('./test/timestamps_os.tsv', 'os')

print(od_dfp)
print(os_dfp)