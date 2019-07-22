import os
import numpy as np
import cv2
import imageio
import multiprocessing as mp

def convert_bin_png(filename, save_folder, im_shape=(1544,2064)):
    '''
    Take a file saved in .bin format from a ximea camera, and convert it to a png image.
    Parameters:
        filename (str): file to be converted
        save_folder (str): folder to save png files
        im_shape (2pule ints): shape of image
    Returns:
        None
    '''
    fname, _ = os.path.splitext(os.path.basename(filename))
    save_filepath = os.path.join(save_folder, fname + '.png')
    binary_img = []
    with open(filename, 'rb') as f:
        byte = f.read(1)
        while(byte):
            byte = f.read(1)
            b = int.from_bytes(byte,'big')
            binary_img.append(b)
        f.close()
    
    im = np.array(binary_img).reshape(im_shape)
    im = cv2.cvtColor(np.uint8(im), cv2.COLOR_BayerGR2RGB)
    imageio.imwrite(save_filepath, im)
    print('*',end='')
    
    return()

def convert_folder(read_folder, write_folder):
    #loop through files in folder
    for f in os.listdir(read_folder):
        if f.endswith(".bin"):
            convert_bin_png(os.path.join(read_folder,f), write_folder)
            print('*')
        
def run_ximea_analysis(capture_folder, analysis_folder):
    '''
    Analyze video data, including converting .bin files to png files.
    '''

    try:
        #OS
        os_cap_folder = os.path.join(capture_folder,'cam_os')
        os_ana_folder = os.path.join(analysis_folder,'cam_os')
        if not os.path.exists(os_ana_folder):
            os.makedirs(os_ana_folder)
        convert_folder(os_cap_folder, os_ana_folder)

        #same for OD
        od_cap_folder = os.path.join(capture_folder,'cam_od')
        od_ana_folder = os.path.join(analysis_folder,'cam_od')
        if not os.path.exists(od_ana_folder):
            os.makedirs(od_ana_folder)
        convert_folder(od_cap_folder, od_ana_folder)

    except Exception as e:
        print(e)
        print('Problem with analzing saved scene camera files. Tell Vasha to make more informative error reporting!')

def run_analysis(subject_name=None, task_name=None, exp_type=None, 
                 read_dir='./capture', save_dir='./analysis'):
    
    '''
    Run a data analysis, on a pre or post calibration, or an experiment.
    Params:
        subject (string): Subject ID to be included in file structure
        task_name (string): Name of task to be included in file structure
        exp_type (string): Type of experiment, either 'pre', 'post', or 'exp'
        save_dir (string): Name of base directly to save experiment files
        
    '''
    
    #create directory structure to find capture files
    read_folder = os.path.join(read_dir, subject_name, task_name, exp_type)
    scene_cam_read_folder = os.path.join(read_folder,'scene_camera')
    eye_cam_read_folder = os.path.join(read_folder,'eye_camera')
    imu_read_folder = os.path.join(read_folder, 'imu')
    
    #create directory structure to save analyzed files
    save_folder = os.path.join(save_dir, subject_name, task_name, exp_type)
    scene_cam_save_folder = os.path.join(save_folder,'scene_camera')
    eye_cam_save_folder = os.path.join(save_folder,'eye_camera')
    imu_save_folder = os.path.join(save_folder, 'imu')
    
    #run sceme camera analysis
    print('Running Frame Analysis...')
    run_ximea_analysis(scene_cam_read_folder, scene_cam_save_folder)
    
    #run eye tracker analysis
    #run IMU analysis
    
    print("Finished Anaysis!")
    
