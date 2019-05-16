import os
import sys

import tensorflow as tf

from absl import app
from absl import flags
from absl import logging

from config import Config

logging.set_verbosity(logging.DEBUG)

FLAGS = flags.FLAGS
flags.DEFINE_string('phase', 'train',
                    'The phase can be train, eval or test')

flags.DEFINE_boolean('load', False,
                        'Turn on to load a pretrained model from either \
                        the latest checkpoint or a specified file')

flags.DEFINE_string('model_file', None,
                    'If specified, load a pretrained model from this file')

# Required flags
# flags.mark_flag_as_required("phase")

def main(argv):
    '''python image_captioning/main.py --log_dir log'''

    del argv  # Unused.
    config = Config()
    config.phase = FLAGS.phase

    print('Running under Python {0[0]}.{0[1]}.{0[2]}'.format(sys.version_info),
        file=sys.stderr)

    if FLAGS.log_dir:
        if not os.path.exists(FLAGS.log_dir):
            os.makedirs(FLAGS.log_dir)
        log_file='absl_logging'
        logging.get_absl_handler().use_absl_log_file(log_file, FLAGS.log_dir)

    logging.info('Running %s phase', config.phase)

if __name__ == '__main__':
  app.run(main)