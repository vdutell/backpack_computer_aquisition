import os
import multiprocessing as mp, queue
import time
from ximea import xiapi
import ximea_cam_aquire_save as ximtools
#import queue

def write_queue_to_file(save_folder, queue):
    '''
    Write queue to file to save timestamps, matching frame number to timestamp'''
    queue_savefile = os.path.join(save_folder,'timestamps.tsv')
    with open(queue_savefile, 'w') as f:
        f.write(f'frame\tos\tod\tcy\n')
        while not queue.empty():
            f.write(queue.get())
            f.write('\n')
            queue.task_done()
        f.close()
    return()
        

def run_queue_worker(queue, save_folder):
    '''
    Start an infinite loop for a process that pops the oldest image from the queue and saves it to disk
    Params:
        queue (queue): the queue to read from
        save_folder (str): name of the folder we write to 
    '''
    i=0
    print('Queue Started')
    #while not queue.empty() & i>10:
    while True:
        #pop a frame from the queue
        try:
            frame_data = queue.get()
            filename = os.path.join(save_folder, f'frame_{i}.bin')
            print(filename)   
            i+=1
        except Empty:
            print('$',end='')
        #save it as a file

        #with open(filename, 'wb') as f:
        #    f.write(frame_data)
        #    f.close()
        #print('#',end='')
        #queue.task_done()
    return()
    

def run_ximea_aquisition(save_folder, frame_rate, max_frames=10):    
    '''
    Aquire images from ximea cameras and save them.
    Parameters:
        save_folder (str): name of folder to save images
        frame_rate (int): how fast should we collect?
        max_frames (int): max number of frames to collect (mostly for testing)
    Returns:
        None
    ''' 
    
    #queues to save camera and timestamp data
    q_ts = queue.Queue()
    q_od = queue.Queue()    
    q_os = queue.Queue()
    q_cy = queue.Queue()   
    
    #camera_settings
    cam_timing_mode='XI_ACQ_TIMING_MODE_FREE_RUN'
    cam_image_format='XI_RAW16'
    cam_exposure=50
    cam_framerate=500 #200
    cam_gain=10
    
    #prep camera od
    cam_od_id = 'XECAS1922000'
    cam_od_folder = os.path.join(save_folder,'cam_od')
    if not os.path.exists(cam_od_folder):
        os.makedirs(cam_od_folder)
        
    #prep camera os
    cam_os_id = 'XECAS1922001'
    cam_os_folder = os.path.join(save_folder,'cam_os')
    if not os.path.exists(cam_os_folder):
        os.makedirs(cam_os_folder)
    
    #prep camera cy
    cam_cy_id = 'DUMMY FOR NOW'
    cam_cy_folder = os.path.join(save_folder,'cam_cy')
    if not os.path.exists(cam_cy_folder):
        os.makedirs(cam_cy_folder)
    
    try:
        #right camera (OD)
        cam_od = xiapi.Camera()
        cam_od.open_device_by_SN(cam_od_id)
        #apply camera settings
        cam_od = ximtools.apply_cam_settings(cam_od,
                                             timing_mode=cam_timing_mode,
                                             exposure=cam_exposure,
                                             framerate=cam_framerate,
                                             gain=cam_gain)
        #left camera (OS)
        cam_os = xiapi.Camera()
        cam_os.open_device_by_SN(cam_os_id)
        #apply camera settings
        cam_os = ximtools.apply_cam_settings(cam_os,
                                             timing_mode=cam_timing_mode,
                                             exposure=cam_exposure,
                                             framerate=cam_framerate,
                                             gain=cam_gain)
 
          #cyclopean camera (CY)
#         cam_cy = xiapi.Camera()
#         cam_cy.open_device_by_SN(cam_cy_id)
#         #apply camera settings
#         cam_cy = ximtools.apply_cam_settings(cam_cy,
#                                              timing_mode=None,
#                                              exposure=cam_exposure,
#                                              framerate=cam_framerate,
#                                              gain=cam_gain)

    
        #start our job saving threads
        os_save_thread = mp.Process(target=run_queue_worker, args=(q_os, cam_os_folder))
        os_save_thread.daemon = True
        os_save_thread.start()      
        
        od_save_thread = mp.Process(target=run_queue_worker, args=(q_od, cam_od_folder))
        od_save_thread.daemon = True
        od_save_thread.start()      
        
        cy_save_thread = mp.Process(target=run_queue_worker, args=(q_cy, cam_cy_folder))
        cy_save_thread.daemon = True
        cy_save_thread.start()      
        
        #add all the job saving threads to the queue
        save_jobs = []
        save_jobs.append(os_save_thread)
        save_jobs.append(od_save_thread)
        save_jobs.append(cy_save_thread)
        
        #setup image handles and start aquisition
        cam_od_im = xiapi.Image()
        cam_od.start_acquisition()
        cam_os_im = xiapi.Image()
        cam_os.start_acquisition()
        #cam_cy_im = xiapi.Image()
        #cam_cy.start_acquisition()
     
        
        for i in range(max_frames):
            print('*',end='')
            
            #get images and timestamps
            cam_os.get_image(cam_os_im)
            cam_os_ts_s = cam_os_im.tsSec
            cam_os_ts_u = cam_os_im.tsUSec
            
            cam_od.get_image(cam_od_im)
            cam_od_ts_s = cam_od_im.tsSec
            cam_od_ts_u = cam_od_im.tsUSec
            
            #cam_cy.get_image(cam_cy_im)
            #cam_cy_ts_s = cam_cy_im.tsSec
            #cam_cy_ts_u = cam_cy_im.tsUSec
            cam_cy_ts_s = cam_od_ts_s
            cam_cy_ts_u = cam_od_ts_u
           
            #pull image from cameras
            cam_od_data = cam_od_im.get_image_data_raw()
            cam_os_data = cam_os_im.get_image_data_raw()
            cam_cy_data = cam_os_data #for now use dummy data 
            
            #calcuate the exact timestamp we took the image, add to timestamp queue
            q_ts.put(f'{i}\t{cam_os_ts_s}.{cam_os_ts_u}\t{cam_od_ts_s}.{cam_od_ts_u}\t{cam_cy_ts_s}.{cam_cy_ts_u}')
            # put cam data in camera frame queues
            q_od.put(cam_od_data)
            q_os.put(cam_os_data)
            q_cy.put(cam_cy_data)
            
            
        print(f'Sampled to max num frames of {max_frames}')
        print('Cleanly Stopping Device Aquisition and closing file.')
        
        #stop acquisition
        cam_od.stop_acquisition()
        cam_os.stop_acquisition()
        #cam_cy.stop_acquisition()
        #stop communication
        cam_od.close_device()
        cam_os.close_device()
        #cam_cy.close_device()
         
        #tell queue runners they can finish
        q_od.task_done()
        q_os.task_done()
        q_cy.task_done()
    
        
        #write queue timestamps
        print('Writing Queue of Timestamps')
        write_queue_to_file(save_folder, q_ts)
        
        #wait for saves
        print('Waiting for save threads to finish')
        for job in save_jobs:
            job.join()

        
    except KeyboardInterrupt:
        print('Detected Keyboard Interrupt. Stopping Acquisition Cleanly')
        
        #stop acquisition
        cam_od.stop_acquisition()
        cam_os.stop_acquisition()
        #cam_cy.stop_acquisition()
        #stop communication
        cam_od.close_device()
        cam_os.close_device()
        #cam_cy.close_device()

        #write queue timestamps
        write_queue_to_file(save_folder, q_ts)

 
    except Exception as e:
        print(e)
        print('There was an Error. Cleanly Stopping Device Aquisition and closing file.')
        
        #stop acquisition
        cam_od.stop_acquisition()
        cam_os.stop_acquisition()
        #cam_cy.stop_acquisition()
        #stop communication
        cam_od.close_device()
        cam_os.close_device()
        #cam_cy.close_device()

        #write queue timestamps
        write_queue_to_file(save_folder, q_ts)

    
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


def run_experiment(subject_name=None, task_name=None, exp_type=None, save_dir='./capture', max_frames=10):
    
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
    if(subject_name==None):
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
    save_folder = os.path.join(save_dir, subject_name, task_name, exp_type)
    scene_cam_folder = os.path.join(save_folder,'scene_camera')
    eye_cam_folder = os.path.join(save_folder,'eye_camera')
    imu_folder = os.path.join(save_folder, 'imu')

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
    
    
    #start collection for scene cameras (ximea)
    print(f'Starting scene aquisition at {frame_rate}fps...')
    run_ximea_aquisition(scene_cam_folder, frame_rate, max_frames=max_frames)
    
    
    return()


