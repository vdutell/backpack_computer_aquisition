import ximea_cam_aquire_save as xim
from ximea import xiapi
import run_analysis as ana

import time

collection_mins = 0.5
save_batchsize = 200

save_folder = './test/testing_framedrops'
save_folder_list= [save_folder, save_folder]

ncams = int(input("how many cameras?"))

print(f'Collecting for {collection_mins*60.} seconds...')
xim.ximea_acquire(save_folder_list, max_collection_mins=collection_mins, ims_per_file=save_batchsize, num_cameras=ncams)

print('Done Recording. Counting Missed Frames...')

percent_dropped_file = f'{save_folder}/aggregate_framedrop.tsv'

cams = ['cy','os','od']
for i in range(ncams):
	with open(percent_dropped_file, 'a+') as f:
		cam_name = cams[i]
		percentage_dropped_frames = ana.count_missed_frames(f'{save_folder}/timestamps_{cam_name}.tsv', cam_name)
		f.write(f"{time.time()}\t{cam_name}\t{percentage_dropped_frames}\n")

