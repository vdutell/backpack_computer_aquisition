import os
from multiprocessing import Process, Queue
import time
import numpy as np
import ximea_cam_aquire_save as xim
import realsense_imu_aquire_save as rls
import pupil_cam_aquire_save as pup


def run_experiment(subject_name=None, 
                   task_name=None, 
                   exp_type=None, 
                   save_dirs='./capture',
                   collection_minutes=1,
                   save_batchsize=100):
    
    '''
    Run a data collection, either pre or post calibration, or an experiment.
    Params:
        subject (string): Subject ID to be included in file structure
        task_name (string): Name of task to be included in file structure
        exp_type (string): Type of experiment, either 'pre', 'post', or 'exp'
        save_dirs (list of strings): Name of base directories to save experiment files
        save_batchsize (int): how many camera frames per file?
        
    '''
    #test for valid input
    valid_experiments=['pre','post','exp']
    if(subject_name==None):
       raise ValueError("Please Specify a Subject ID!")
    
    if(exp_type not in valid_experiments):
       raise ValueError(f"Please Specify an experiment type: {valid_experiments}")
    
    #set parameters
#     if(exp_type=='exp'):
#         frame_rate = 200
#         print('Running an experiment.')
#     elif(exp_type=='pre'):
#         frame_rate = 20
#         print('Running a calibration.')
    
    #create directory structure for saving
    scene_cam_folders = [os.path.join(save_dir, subject_name, task_name, exp_type,
                                      'scene_camera') for save_dir in save_dirs]
    eye_cam_folder = os.path.join(save_dirs[0], subject_name, task_name, exp_type,'eye_camera')
    imu_folder = os.path.join(save_dirs[0], subject_name, task_name, exp_type,'imu')
    
    print(eye_cam_folder)

    #start collection for eye tracker (pupil labs)
    eyetracker_thread = Process(target=pup.run_pupillabs_aquisition, 
                                        args=(eye_cam_folder,
                                             collection_minutes))
    eyetracker_thread.daemon = True  # Daemonize thread
    eyetracker_thread.start()        # Start the execution   
    print(f'Started eyetracking aquisition...')
    

    #start collection for IMUS (intel realsense)
    imu_thread = Process(target=rls.run_realsense_aquisition, 
                                        args=(imu_folder,
                                              collection_minutes))
    imu_thread.daemon = True  # Daemonize thread
    imu_thread.start()        # Start the execution   
    print(f'Started imu aquisition...')    
    
    
    #start collection for scene cameras (ximea)
    print(f'Starting scene aquisition...')
    scene_camera_thread = xim.ximea_acquire(scene_cam_folders,
                                      collection_minutes, 
                                      save_batchsize)
    
    print(f'All Done! Collected for {collection_minutes} minutes')

    return()


