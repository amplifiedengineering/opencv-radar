import argparse 
from traffic_counter import TrafficCounter

def CLI():
    #Define default values here to make documentation self-updating
    minArea_default       = 200
    direction_default     = ['H', '924', '1400']
    numCount_default      = 10
    videoWidth_default    = 640
    videoParams_default   = ['mjpg','avi']
    startingFrame_default = 10

    parser = argparse.ArgumentParser(description='Finds the contours on a video file')          #creates a parser object
    parser.add_argument('-p','--path',type=str,help="""A video filename or path.
    Works better with .avi files.
    If no path or name is provided, the camera will be used instead.""")        #instead of using metavar='--path', just type '--path'. For some reason the metavar argument was causing problems

    parser.add_argument('-d','--direction', type=str,default=direction_default,nargs=3,help=f"""A character: H or V
    representing the orientation of the count line. H is horizontal, V is vertical.
    If not provided, the default is {direction_default[0]},{direction_default[1]}, {direction_default[2]}. The second and third parameters
    are pixels where the start and end measurement is.""")
    parser.add_argument('-l', '--length', type=str, help="""Distance between the measurement lines to ensure
    capturing the speed of the vehicles""")
    args = parser.parse_args()
    return args

def make_video_params_dict(video_params):
    codec     = video_params[0]
    extension = video_params[1]
    
    params_dict = {
        'codec'    :codec,
        'extension':extension,
    }
    return params_dict

def main(args):

    video_source   = args.path
    line_direction = args.direction[0]
    line_position_start  = int(args.direction[1])
    line_position_end = int(args.direction[2])
    distance = int(args.length)
    tc = TrafficCounter(video_source,
                        line_direction,
                        line_position_start,
                        line_position_end,
                        distance,)

    tc.main_loop()

if __name__ == '__main__':
    args = CLI()
    main(args)