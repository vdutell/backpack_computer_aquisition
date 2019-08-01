import copy
import multiprocessing as mp
import time
import os
import numpy as np
from ximea import xiapi
from collections import namedtuple

frame_data = namedtuple("frame_data", "raw_data nframe tsSec tsUSec")

default_settings = {"timing_mode":  'XI_ACQ_TIMING_MODE_FREE_RUN',
                    "img_format": "XI_RAW8",
                    'framerate': 200,
                    'gain': 10}


def get_sync_string(cam_name, cam_handle):
    '''
    Clock camera and wall clocks together to ensure they match
    Params:
        cam_name (str): String name of camera (ie cam_od/cam_os/cam_cy
        cam_handle (XimeaCamera instance): camera handle to query time
    Returns:
        sync_string (str): string to write to file with cam name, time, and wall time
    '''
    t_wall_1 = time.monotonic()
    t_cam = cam_handle.get_param('timestamp')
    t_cam = t_cam/(1e9) #this is returned in nanoseconds, change to seconds
    t_wall_2 = time.monotonic()
    t_wall = np.mean((t_wall_1, t_wall_2)) #take middle of two wall times
    dt = t_cam - t_wall
    sync_string = f'{cam_name}\t{t_wall}\t{t_cam}\t{dt}'
    return(sync_string)


def apply_cam_settings(cam, timing_mode=None, exposure=None, framerate=None,
                        gain=None, img_format=None,
                        auto_wb=None, transport_packing=None,
                        ):
    """
    Apply settings to the camera
    """

    if exposure is not None:
        cam.set_exposure(exposure)
    if timing_mode is not None:
        cam.set_acq_timing_mode(timing_mode)
    if framerate is not None:
        cam.set_framerate(framerate)
    if gain is not None:
        cam.set_gain(gain)
    if img_format is not None:
        cam.set_imgdataformat(img_format)
    if auto_wb is not None:
        cam.set_param('auto_wb', 1)
    if transport_packing is not None:
        cam.set_imgdataformat('XI_RAW16')
        cam.set_param('output_data_bit_depth', 16) #12
        cam.enable_transport_packing()

            
def save_queue_worker(cam_name, save_queue, save_folder):
    
    i = 0
    if not os.path.exists(os.path.join(save_folder, cam_name)):
        os.makedirs(os.path.join(save_folder, cam_name))

    ts_file_name = os.path.join(save_folder, f"timestamps_{cam_name}.tsv")
    while True:
        bin_file = os.path.join(save_folder, cam_name, f'frame_{i}.bin')
        image = save_queue.get()

        with open(bin_file, 'wb') as f, open(ts_file_name, 'a+') as ts_file:
            f.write(image.raw_data)
            ts_file.write(f"{i}\t{image.nframe}\t{image.tsSec}.{image.tsUSec}\n")
            
        i+=1

def acquire_camera(cam_id, cam_name, sync_queue, save_queue, max_frames, **settings):
    """
    Acquire frames from a single camera.
    
    Parameters:
        cam_id (str):  The serial number of the camera
        cam_name (str): A text name for the camera
        sync_queue (Multithreading.Queue): A queue which accepts the sync strings
        save_queue (Mutlithreading.Queue): A queue which accepts xiapi.Images
        max_frames (int): the maximum number of frames to run
        
        Any keywords which are present in default_settings may also be passed as 
        keyword arguments to this function as well.
        IE:
            acquire_camera("some_id",
                           "a camera",
                           Q,
                           Q2,
                           10,
                           timing_mode=None,
                           framerate=None, ...)
   
    """  
    
    s = copy.deepcopy(default_settings)
    s.update(settings)
    settings = s
    
    settings['exposure'] = np.int(np.around(1e6*(1.0/settings['framerate'])))
    
    exp_time = settings['exposure'] / 1000
    print(f"Setting cam exposure to {exp_time} ms")
    
    try:
        camera = xiapi.Camera()
        camera.open_device_by_SN(cam_id)
        
        print('Recording Timestamp Syncronization Pre...')
        sync_str = get_sync_string(cam_name + "_pre", camera)
        sync_queue.put(sync_str)
        
        apply_cam_settings(camera, **settings)
        
        camera.start_acquisition()
        
        image = xiapi.Image()
        for _ in range(max_frames):
            camera.get_image(image)
            save_queue.put(frame_data(image.get_image_data_raw(),
                                      image.nframe,
                                      image.tsSec,
                                      image.tsUSec))
        
    except KeyboardInterrupt:
        print('Detected Keyboard Interrupt. Stopping Acquisition')
        sync_str = get_sync_string(cam_name + "_post", camera)
        sync_queue.put(sync_str)
        
    finally:
        print(f"Camera {cam_name} Cleanup...")
        camera.stop_acquisition()
        camera.close_device()
    
        print(f"Camera {cam_name} aquisition finished")
        

def ximea_acquire(save_folder, max_frames=100, **settings):
    
    # queues do we need?
    # 3 x save_queues
    # 3 x sync_queues
    
    cameras = {'od': "XECAS1922000",
               'os': "XECAS1922001"}
    
    save_queues = [mp.Queue() for _ in cameras]
    sync_queues = [mp.Queue() for _ in cameras]
    
    if not os.path.exists(save_folder):
        os.makedirs(save_folder)
        
    save_threads = []
    for i, cam in enumerate(cameras):
        proc = mp.Process(target=save_queue_worker,
                                       args=(cam,
                                             save_queues[i],
                                             save_folder))
        proc.daemon = True
        proc.start()
        save_threads.append(proc)
        
    acquisition_threads = []
    for i, (cam_name, cam_sn) in enumerate(cameras.items()):
        proc = mp.Process(target=acquire_camera,
                          args=(cam_sn,
                                cam_name,
                                sync_queues[i],
                                save_queues[i],
                                max_frames),
                          kwargs=settings)
        acquisition_threads.append(proc)
        proc.daemon = True
    
    print("Starting acquisition threads.")
    for proc in acquisition_threads:
        proc.start()
    
    print("Waiting for acquisition to finish.")
    for proc in acquisition_threads:
        proc.join()
    
    for q in save_queues:
        while not q.empty():
            time.sleep(0.1)