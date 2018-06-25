
import pickle, argparse, json, os, sys
import tensorflow as tf
import numpy as np


argparser = argparse.ArgumentParser(
    description='dourflow: a keras YOLO V2 implementation.')


argparser.add_argument(
    'action',
    help='what to do: \'train\', \'validate\' or pass an image file/dir.')


argparser.add_argument(
    '-m',
    '--model',
    help='path to input yolo v2 keras model',
    default='yolo_model.h5')


argparser.add_argument(
    '-c',
    '--conf',
    help='path to configuration file',
    default='config.json')


argparser.add_argument(
    '-t',
    '--threshold',
    type=float,
    help='detection threshold',
    default=0.3)


argparser.add_argument(
        '-w',
        '--weight_file',
        help='path to weight file',
        default='weights.h5')


args = argparser.parse_args()


action = args.action
config_path = args.conf


with open(config_path) as config_buffer:    
        config = json.loads(config_buffer.read())



def generate_yolo_grid(batch, g, num_bb):
    c_x = tf.to_float(tf.reshape(tf.tile(tf.range(g), [g]), (1, g, g, 1, 1)))
    c_y = tf.transpose(c_x, (0,2,1,3,4))
    return tf.tile(tf.concat([c_x, c_y], -1), [batch, 1, 1, num_bb, 1])




def get_threshold(value):
    if value > 1. or value < 0:
        raise ValueError('Please enter a valid threshold (between 0. and 1.).')
    return value



class YoloParams(object):
    
    # Mode
    PREDICT_IMAGE = ''
    WEIGHT_FILE = ''
    if action != 'gen':
        if action == 'validate' or action == 'train':
            YOLO_MODE = action
        else:
            if os.path.isdir(action):
                YOLO_MODE = 'inference'
            elif os.path.isfile(action):
                if action.split('.')[1] in ['mp4','avi','wmv','mpg','mpeg']:
                    YOLO_MODE = 'video'
                else:
                    YOLO_MODE = 'inference'
            else:
                raise ValueError('First argument for dourflow must be: \'training\','
                    ' \'validation\' or an image file/dir.')    

            PREDICT_IMAGE = action
    else:
        assert args.weight_file, "Need to pass weight file if generating model."
        # Paths
        WEIGHT_FILE = args.weight_file

    TRAIN_IMG_PATH = config['train']['image_folder'] 
    TRAIN_ANN_PATH = config['train']['annot_folder']

    VALIDATION_IMG_PATH = config['valid']['image_folder']
    VALIDATION_ANN_PATH = config['valid']['annot_folder']
    VALIDATION_OUT_PATH = config['valid']['pred_folder']

    # Model    
    #IN_MODEL = config['config_path']['in_model']
    IN_MODEL = args.model
    OUT_MODEL_NAME = config['train']['out_model_name']
    
    ARCH_FNAME = config['config_path']['arch_plotname']

    # Classes
    CLASS_LABELS = [x.rstrip() for x in open(config['config_path']['labels'])]
    NUM_CLASSES = len(CLASS_LABELS)
    CLASS_TO_INDEX = dict(zip(CLASS_LABELS, np.arange(NUM_CLASSES)))
    CLASS_WEIGHTS = np.ones(NUM_CLASSES, dtype='float32')

    # Infrastructure params
    INPUT_SIZE = config['model']['input_size']
    GRID_SIZE = config['model']['grid_size']
    TRUE_BOX_BUFFER = config['model']['true_box_buffer']
    ANCHORS = [float(a) for a in open(config['config_path']['anchors']).read().split(', ')]

    NUM_BOUNDING_BOXES = len(ANCHORS) // 2
    OBJECT_SCALE = 5.0
    NO_OBJECT_SCALE  = 1.0
    CLASS_SCALE = 1.0
    COORD_SCALE = 1.0

    # Train params
    BATCH_SIZE = config['train']['batch_size']
    L_RATE = config['train']['learning_rate']
    NUM_EPOCHS = config['train']['num_epochs']
    TRAIN_VERBOSE = config['train']['verbose']

    # Thresholding
    IOU_THRESHOLD = get_threshold(config['model']['iou_threshold'])
    NMS_THRESHOLD = get_threshold(config['model']['nms_threshold'])
    DETECTION_THRESHOLD = get_threshold(args.threshold)

    # Additional / Precomputing  
    c_grid = generate_yolo_grid(BATCH_SIZE, GRID_SIZE, NUM_BOUNDING_BOXES)
    anchors = np.reshape(ANCHORS, [1,1,1,NUM_BOUNDING_BOXES,2])

