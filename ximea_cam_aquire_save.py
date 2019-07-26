from ximea import xiapi
import pickle as pickle
import time
import traceback

def print_cam_settings(cam):
    """
    Print current camera settings
    """
    #Exposure
    print(f'Exposure is set to {cam.get_exposure()} us = {cam.get_exposure()/1000} ms')
    #Gain
    print(f'Gain is set to {cam.get_gain()}')
    #aquisition mode
    print(f'Mode is set to {cam.get_acq_timing_mode()}')
    #Framerate
    print(f'Framerate is set to {cam.get_framerate()} fps')
    #data format
    print(f'Data format is set to {cam.get_imgdataformat()}')
    #white balance
    #print(f'White balance is set to {cam.get_autowb()}')

    return()

def apply_cam_settings(cam, timing_mode=None, exposure=None, framerate=None,
                        gain=None, img_format=None, img_bpp=None,
                        auto_wb=None, transport_packing=None,
                        ):
    """
    Apply settings to the camera
    """

    #Exposure:
    if(exposure):
        cam.set_exposure(exposure)
    #Mode:
    if(timing_mode):
        cam.set_acq_timing_mode(timing_mode)
    #Framerate:
    if(framerate):
        cam.set_framerate(framerate)
    #Gain:
    if(gain):
        cam.set_gain(gain)
    #Format:
    if(img_format):
        cam.set_imgdataformat(img_format)
    #BPP Sensor:
    if(img_bpp):
        cam.set_imgdataformat(img_format)
    #White Blalance
    if(auto_wb):
        cam.set_param('auto_wb', 1)
        #cam.set_auto_wb(auto_wb)
    if(transport_packing):
        cam.set_imgdataformat('XI_RAW16')
        camp.set_param('output_data_bit_depth', 16) #12
        cam.enable_transport_packing()
        
    return(cam)
    

def aquire_save_fullset(num_frames=10, cam_timing_mode='XI_ACQ_TIMING_MODE_FREE_RUN', 
                        cam_exposure=500, 
                         cam_framerate=1000, cam_gain=1, img_format='XI_RAW8',
                         img_autowb=1,
                         verbose=True):
    """
    Aquire a set of files and only save after they have all been collected
    """
    #create instance for first connected camera
    cam = xiapi.Camera()

    #start communication

    if(verbose):
        print('Opening first camera...')
    cam.open_device()
    #to open specific device, use:
    #cam.open_device_by_SN('1922001')
    #(open by serial number)

    try:

        #apply settings to our camera device
        cam = apply_cam_settings(cam, timing_mode=cam_timing_mode, exposure=cam_exposure, 
                                framerate=cam_framerate, gain=cam_gain, img_format=img_format,
                                auto_wb=img_autowb)
        if(verbose):
            print_cam_settings(cam)

        #create instance of Image to store image data and metadata
        img = xiapi.Image()

        #start data acquisition
        if(verbose):
            print(f'Starting data acquisition of {num_frames} frames...',end='')
        cam.start_acquisition()

        ims = []

        #time start
        tic = time.clock()
        for i in range(num_frames):
            if(verbose):
                print('*',end='')
            #get data and pass them from camera to img
            cam.get_image(img)

            #get raw data from camera
            #for Python2.x function returns string
            #for Python3.x function returns bytes
            data_raw = img.get_image_data_raw()
            ims.append(data_raw)

        #time stop
        toc = time.clock()
        if(verbose):
            print(f'\nEffective Speed: {num_frames/(toc-tic):.2f} FPS')

        #stop data acquisition
        if(verbose):
            print('Stopping acquisition...')
        cam.stop_acquisition()

        #stop communication
        cam.close_device()

        #save data: write to bitearray
        if(verbose):
            print(f'Saving data...', end='')
        for i in range(len(ims)):
            with open(f'capture/batch/data_raw_bytes_{i}.bin', 'wb') as f:
                f.write(ims[i])
                if(verbose):
                    print('*',end='')
        if(verbose):
            print(f'Done!') 

        if(verbose):
            print('Done.')
        
        return()

    except Exception as e:
        print('Something Failed. Cleanly closing the device.')
        #stop communication
        cam.close_device()

        return(e)