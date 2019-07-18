import os
import multiprocessing as mp
import time
from ximea import xiapi

def aquire_save_frames(save_folder, frame_rate, cam_id, maxframes=100):
    '''
    Aquire frames and save them to our directory in an infinite loop
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
        camid (str): name of camera ID we are opening
        maxframes (int): max number of frames to collect
    Returns:
        None
    '''
    # make directory if it doesn't exist yet
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
    
    #open camera and start collecting and saving frames
    try:
        #create camera, open it, and make image instance
        cam = xiapi.Camera()
        cam.open_device_by_SN(cam_id)
        #TODO: apply settings to camera *******
        img = xiapi.Image()
        cam.start_acquisition()

        for i in range(maxframes):
            #get and image and store it
            cam.get_image(img)
            data_raw = img.get_image_data_raw()
            with open(os.path.join(save_folder,f'data_raw_bytes_{i}.bin'), 'wb') as f:
                f.write(data_raw)
                f.close()
    
    except Exception as e:
        print(e)
        print('Cleanly Stopping Device Aquisition and closing file.')
        cam.close_device()
    

def run_ximea_aquisition(save_folder, frame_rate):
    '''
    Aquire images from ximea cameras and save them.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
    Returns:
        None
    '''
    #open campera od
    cam_od_id = 'XECAS1922000'
    cam_od_folder = os.path.join(save_folder,'cam_od')
    cam_od_thread = mp.Process(target=aquire_save_frames, 
                                        args=(cam_od_folder, frame_rate, cam_od_id))
    cam_od_thread.daemon = True  # Daemonize thread
    cam_od_thread.start()        # Start the execution
    
    #open campera os
    cam_os_id = 'XECAS1922001'
    cam_os_folder = os.path.join(save_folder,'cam_os')
    cam_os_thread = mp.Process(target=aquire_save_frames, 
                                        args=(cam_os_folder, frame_rate, cam_os_id))
    cam_os_thread.daemon = True  # Daemonize thread
    cam_os_thread.start()        # Start the execution


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


def run_experiment(subject=None, task_name=None, exp_type=None, save_dir='./capture'):
    
    '''
    Run a data collection, either pre or post calibration, or an experiment.
    Params:
        subject (string): Subject ID to be included in file structure
        task_name (string): Name of task to be included in file structure
        exp_type (string): Type of experiment, either 'pre', 'post', or 'exp'
        save_dir (string): Name of base directly to save experiment files
        
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
    save_folder = os.path.join(save_dir, subject, task_name, exp_type)
    scene_cam_folder = os.path.join(save_folder,'scene_camera')
    eye_cam_folder = os.path.join(save_folder,'eye_camera')
    imu_folder = os.path.join(save_folder, 'imu')

    #start collection for scene cameras (ximea)
    #scenecam_thread = mp.Process(target=run_ximea_aquisition, 
    #                                    args=(scene_cam_folder, frame_rate))
    #scenecam_thread.daemon = True  # Daemonize thread
    #scenecam_thread.start()        # Start the execution
    run_ximea_aquisition(scene_cam_folder, frame_rate)
    print(f'Started scene aquisition at {frame_rate}fps...')
    
    #start collection for eye tracker (pupil labs)
    eyetracker_thread = mp.Process(target=run_pupillabs_aquisition, 
                                        args=(eye_cam_folder, frame_rate))
    eyetracker_thread.daemon = True  # Daemonize thread
    eyetracker_thread.start()        # Start the execution   
    print(f'Started eyetracking aquisition at {frame_rate}fps...')

    #start collection for IMUS (intel realsense)
    imu_thread = mp.Process(target=run_realsense_aquisition, 
                                        args=(imu_folder, frame_rate))
    imu_thread.daemon = True  # Daemonize thread
    imu_thread.start()        # Start the execution   
    print(f'Started imu aquisition at {frame_rate}fps...')    
    
    return()