import ximea_cam_aquire_save as xim
import run_analysis as ana
import numpy as np
import os
import run_experiment as runexp

subject = 'ag'
task = 'laptop_1'
exp = 'pre'
capture_dir_list = ['/home/vasha/Desktop/backpack_computer_aquisition/capture']
path = os.path.join(capture_dir_list[0], subject, task, exp,'test')
if not os.path.exists(path):
    oldmask = os.umask(000)
    os.makedirs(path, 777)
    os.umask(oldmask)

collection_minutes = 3
save_batchsize = 200
ncameras = 1

pupil_port = 50020

runexp.run_experiment(subject_name=subject,
                      task_name=task,
                      exp_type=exp,
                      save_dirs=capture_dir_list,
                      collection_minutes=collection_minutes,
                      save_batchsize=save_batchsize,
                      pupil_port=pupil_port,
                      n_cameras = ncameras)
