# def save_frame(frame_data, i, save_folder):
#     '''
#     Save frame to file
#     Params:
#         frame_data (binary str): raw data from camera to be saved
#         i (int): frame number
#         save_folder (str): name of folder to save in
#     Returns:
#         success_flag (bool): were we sucessfull in saving?
#     '''    
#     filename = os.path.join(save_folder, f'frame_{i}.bin')
#     with open(filename, 'wb') as f:
#         f.write(frame_data)
#         f.close()
#         print('#',end='')
        
#     return()


        
        
#         #set camera 1 as master
#         cam_od.set_trigger_source('XI_TRG_SOFTWARE')
#         cam_od.set_trigger_selector('XI_TRG_SEL_EXPOSURE_ACTIVE')
#         cam_od.set_gpi_mode('XI_GPO_EXPOSURE_ACTIVE')
#         #set camera 2 as slave
#         cam_os.set_trigger_selector('XI_TRG_SEL_EXPOSURE_ACTIVE')
#         cam_os.set_gpi_mode('GPO_EXPOSURE_ACTIVE')
#         cam_od.set_gpi_source('XI_TRG_EDGE_RISING')

#         #         xiSetParamInt(handle2, XI_PRM_GPI_SELECTOR, 1);
# #         xiSetParamInt(handle2, XI_PRM_GPI_MODE,  XI_GPI_TRIGGER);
# #         xiSetParamInt(handle2, XI_PRM_TRG_SOURCE, XI_TRG_EDGE_RISING);
        
#         left_cam.set_trigger_source('XI_TRG_EDGE_RISING')
#         right_cam.set_trigger_source('XI_TRG_EDGE_RISING')
# left_cam.set_trigger_selector('XI_TRG_SEL_EXPOSURE_ACTIVE')
# right_cam.set_trigger_selector('XI_TRG_SEL_EXPOSURE_ACTIVE')

# left_cam.set_gpi_mode('XI_GPI_TRIGGER')
# right_cam.set_gpi_mode('XI_GPI_TRIGGER')


#         // set trigger mode on camera1 - as master
#         xiSetParamInt(handle1, XI_PRM_TRG_SOURCE, XI_TRG_SOFTWARE);
#         xiSetParamInt(handle1, XI_PRM_GPO_SELECTOR, 1);
#         xiSetParamInt(handle1, XI_PRM_GPO_MODE,  XI_GPO_EXPOSURE_ACTIVE); // Note1
#         // set trigger mode on camera2 - as slave
#         xiSetParamInt(handle2, XI_PRM_GPI_SELECTOR, 1);
#         xiSetParamInt(handle2, XI_PRM_GPI_MODE,  XI_GPI_TRIGGER);
#         xiSetParamInt(handle2, XI_PRM_TRG_SOURCE, XI_TRG_EDGE_RISING);
#         // start
#         xiStartAcquisition(handle1);
#         xiStartAcquisition(handle2);
#         Sleep(1234); // wait for right moment to trigger the exposure
#         // trigger acquisition on Master camera
#         xiSetParamInt(handle1, XI_PRM_TRG_SOFTWARE, 1);
#         // get image from both cameras
#         xiGetImage(handle1, 100, &image1);
#         xiGetImage(handle2, 100, &image2);

            
        #HANDLE handle;
        # xiOpenDevice(0, &handle);
        # // set trigger mode
        # xiSetParamInt(handle, XI_PRM_TRG_SOURCE, XI_TRG_SOFTWARE);
        # // set digital output 1 mode
        # xiSetParamInt(handle, XI_PRM_GPO_SELECTOR, 1);
        # xiSetParamInt(handle, XI_PRM_GPO_MODE,  XI_GPO_FRAME_ACTIVE);
        # xiStartAcquisition(handle);

        # Sleep(1234); // wait for right moment to trigger the exposure
        # xiSetParamInt(handle, XI_PRM_TRG_SOFTWARE, 1);
        # xiGetImage(handle, 100, &image);
        # // process image1 here
        # Sleep(10); // on most cameras the next trigger should be delayed
        # xiSetParamInt(handle, XI_PRM_TRG_SOFTWARE, 1);
        # xiGetImage(handle, 100, &image);
        # // process image2 here

        #print str(increment_val)
        #get data and pass them from camera to img
        ##    left_cam.get_image(img_left)
        ##    right_cam.get_image(img_right)
        #left_cam.get_image(img_left)
        #right_cam.get_image(img_right)

        #get raw data from camera
        #for Python2.x function returns string
        #for Python3.x function returns bytes
        #left_cam_data = img_left.get_image_data_numpy()
        #right_cam_data = img_right.get_image_data_numpy()
        
        
        
#             #save OD camera
#             od_save_thread = mp.Process(target=save_frame, 
#                                         args=(cam_od_data, i,
#                                               cam_od_folder))
#             od_save_thread.daemon = True
#             od_save_thread.start()      
#             save_jobs.append(od_save_thread)
            
#             #save OS camera
#             os_save_thread = mp.Process(target=save_frame, 
#                                         args=(cam_os_data, i,
#                                               cam_os_folder))  
#             os_save_thread.daemon = True
#             os_save_thread.start()
#             save_jobs.append(os_save_thread)
            
#             #save cyclopean camera
#             cyclop_save_thread = mp.Process(target=save_frame, 
#                                         args=(cam_cy_data, i,
#                                               cam_cy_folder))  
#             cyclop_save_thread.daemon = True
#             cyclop_save_thread.start()
#             save_jobs.append(cyclop_save_thread)



# def aquire_save_frames(save_folder, frame_rate, cam_id, maxframes=100):
#     '''
#     Aquire frames and save them to our directory in an infinite loop
#     Parameters:
#         save_folder (str): name of folder to save images
#         frame_rate (int): how fast should we collect?
#         camid (str): name of camera ID we are opening
#         maxframes (int): max number of frames to collect
#     Returns:
#         None
#     '''
#     # make directory if it doesn't exist yet
#     if not os.path.exists(save_folder):
#         os.makedirs(save_folder)
    
#     #open camera and start collecting and saving frames
#     try:
#         #create camera, open it, and make image instance
#         cam = xiapi.Camera()
#         cam.open_device_by_SN(cam_id)
#         #TODO: apply settings to camera *******
#         img = xiapi.Image()
#         cam.start_acquisition()

#         for i in range(maxframes):
#             #get and image and store it
#             cam.get_image(img)
#             data_raw = img.get_image_data_raw()
#             save_thread = mp.Process(target=save_frame, 
#                                      args=cam_id)
#             save_thread.daemon = True
#             save_thread.start()
    
    
#     except Exception as e:
#         print(e)
#         print('Cleanly Stopping Device Aquisition and closing file.')
#         cam.close_device()
    
#     return()
    

# def run_ximea_aquisition(save_folder, frame_rate):
#     '''
#     Aquire images from ximea cameras and save them.
#     Parameters:
#         save_folder (str): name of folder to save images
#         frame_rate (int): how fast should we collect?
#     Returns:
#         None
#     '''
#     #open campera od
#     cam_od_id = 'XECAS1922000'
#     cam_od_folder = os.path.join(save_folder,'cam_od')
#     cam_od_thread = mp.Process(target=aquire_save_frames, 
#                                         args=(cam_od_folder, frame_rate, cam_od_id))
#     cam_od_thread.daemon = True  # Daemonize thread
#     cam_od_thread.start()        # Start the execution
    
#     #open campera os
#     cam_os_id = 'XECAS1922001'
#     cam_os_folder = os.path.join(save_folder,'cam_os')
#     cam_os_thread = mp.Process(target=aquire_save_frames, 
#                                         args=(cam_os_folder, frame_rate, cam_os_id))
#     cam_os_thread.daemon = True  # Daemonize thread
#     cam_os_thread.start()        # Start the execution