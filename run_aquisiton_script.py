import ximea_cam_aquire_save as xim
import run_experiment as runexp
import run_analysis as runana

import imp
import numpy as np
import matplotlib.pyplot as plt
import imageio

import cv2
import schedule
import time

#settings
subject = 'buddy_stationary'
task = 'chat_1'
exp = 'pre'
capture_dir_list = ['./capture]
analysis_dir = './analysis'

collection_minutes = 1
save_batchsize = 200

imp.reload(runexp)
imp.reload(xim)
runexp.run_experiment(subject_name=subject, 
                      task_name=task, 
                      exp_type=exp,
                      save_dirs=capture_dir_list,
                      collection_minutes=collection_minutes,
                      save_batchsize=save_batchsize)