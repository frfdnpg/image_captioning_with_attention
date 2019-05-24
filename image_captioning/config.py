class Config(object):
    """ Wrapper class for various (hyper)parameters.
    
    """

    def __init__(self):
        # about the model architecture
        self.cnn = 'inception_v3'               # 'inception_v3' or 'nasnet'
        self.rnn = 'gru'                        #  'gru' or 'lstm'
        self.max_caption_length = 20
        self.embedding_dim = 256
        self.rnn_units = 512

        # about the weight initialization and regularization
        self.weight_initilization_method = 'glorot'     # 'glorot', 'xavier', etc.

        # about the optimization
        self.num_epochs = 50
        self.batch_size = 64
        self.optimizer = 'Adam'    # 'Adam', 'RMSProp', 'Momentum' or 'SGD'
        # self.loss = 'sparse_categorical_crossentropy'

        # about the dataset
        self.dataset_name = 'COCO_2014'
        self.buffer_size = 1000

        # about the saver (checkpoint manager)
        self.max_checkpoints = 5
        self.checkpoints_dir = './models/'
        self.summary_dir = './summary/'

        # about the vocabulary
        self.vocabulary_file = './data/vocabulary.pickle'
        self.vocabulary_size = 10000

        # about image features
        self.extract_image_features = True
        self.image_features_batchsize = 16
        # self.image_features_dir = './data/features/'

        # about the training
        self.resume_from_checkpoint = True
        self.num_train_examples =  None
        self.train_image_dir = './data/coco/train2014/'
        self.train_captions_file = './data/coco/annotations/captions_train2014.json'

        # about the evaluation
        self.num_eval_examples =  128
        self.eval_image_dir = './data/coco/val2014/'
        self.eval_captions_file = './data/coco/annotations/captions_val2014.json'
        self.eval_result_dir = './results/eval'
        self.eval_result_file = './results/eval_results.json'
        self.save_eval_result_as_image = False

        # about the inference
        self.test_image_dir = './results/test/images/'
        self.test_result_dir = './results/test/'
        self.test_result_file = './results/test_results.csv'