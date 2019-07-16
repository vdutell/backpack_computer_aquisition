def run_experiment(subject=None, exp_type=None):
    
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
    
    #start collection for scene cameras (ximea)
    #start collection for eye tracker (pupil labs)
    #start collection for IMUS (intel realsense)
    
    print('Experiment Completed Sucessfully!')
    return()