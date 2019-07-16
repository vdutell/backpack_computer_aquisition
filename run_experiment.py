import os
import threading
import time

def run_ximea_aquisition(save_folder, frame_rate):
    '''
    Aquire images from ximea cameras and save them.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
    Returns:
        None
    '''
    time.sleep(10)
    print('Finished Ximea Aquisition.')

def run_pupillabs_aquisition(save_folder, frame_rate):
    '''
    Aquire eyetracking from pupil labs tracker and save it.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
    Returns:
        None
    '''
    time.sleep(5)
    print('Finished PupilLabs Aquisition.')

def run_realsense_aquisition(save_folder, frame_rate):
    '''
    Aquire IMU data from realsense trackers and save it.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
    Returns:
        None
    '''
    time.sleep(5)
    print('Finished Realsense Aquisition.')


def run_experiment(subject=None, exp_type=None, save_dir='./capture'):
    
    '''
    Run a data collection, either pre or post calibration, or an experiment.
    Params:
        subject (string): Subject ID to be included in filename
        exp_type (string): Type of experiment, either 'pre', 'post', or 'exp'
        
    '''
    #test for valid input
    valid_experiments=['pre','post','exp']
    if(subject==None):
       raise ValueError("Please Specify a Subject ID!")
    
    if(exp_type not in valid_experiments):
       raise ValueError(f"Please Specify an experiment type: {valid_experiments}")
    
    #set parameters
    if(exp_type=='exp'):
        frame_rate = 200
        print('Running an experiment.')
    elif(exp_type=='pre'):
        frame_rate = 20
        print('Running a calibration.')
    
    print(f'Collecting at {frame_rate} fps.')
    
    #create directory structure for saving
    save_folder = os.path.join(save_dir, subject, exp_type)
    scene_cam_folder = os.path.join(save_folder,'scene_camera')
    eye_cam_folder = os.path.join(save_folder,'eye_camera')
    imu_folder = os.path.join(save_folder, 'imu')

    #start collection for scene cameras (ximea)
    scenecam_thread = threading.Thread(target=run_ximea_aquisition, 
                                        args=(scene_cam_folder, frame_rate))
    scenecam_thread.daemon = True  # Daemonize thread
    scenecam_thread.start()        # Start the execution
    print(f'Started scene aquisition at {frame_rate}fps...')
    
    #start collection for eye tracker (pupil labs)
    eyetracker_thread = threading.Thread(target=run_pupillabs_aquisition, 
                                        args=(eye_cam_folder, frame_rate))
    eyetracker_thread.daemon = True  # Daemonize thread
    eyetracker_thread.start()        # Start the execution   
    print(f'Started eyetracking aquisition at {frame_rate}fps...')

    #start collection for IMUS (intel realsense)
    imu_thread = threading.Thread(target=run_realsense_aquisition, 
                                        args=(imu_folder, frame_rate))
    imu_thread.daemon = True  # Daemonize thread
    imu_thread.start()        # Start the execution   
    print(f'Started imu aquisition at {frame_rate}fps...')    
    
    return()