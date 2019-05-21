import time

import tensorflow as tf

from absl import logging
from dataset import prepare_train_data
from models import build_model
from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.train import Checkpoint, CheckpointManager
from util import plot_loss

def compute_loss(labels, predictions, loss_function):
    """Computes loss given labels, predictions and a loss function.
    
    Args:
        labels (tensor): ground-truth values
        predictions (tensor): predicted values
        loss_function (tf.keras.losses.Loss): object implementing a loss function, eg. MAE
    
    Returns:
        tensor: computed loss values

    """

    mask = tf.math.logical_not(tf.math.equal(labels, 0))
    loss_ = loss_function(labels, predictions)

    mask = tf.cast(mask, dtype=loss_.dtype)
    loss_ *= mask

    return tf.reduce_mean(loss_)

def get_checkpoint_manager(model, optimizer, checkpoints_dir, max_checkpoints):
    """Obtains a checkpoint manager to save the model while training.
    
    Args:
        model (mode.ImageCaptionModel): object containing encoder, decoder and tokenizer
        optimizer (tf.optimizers.Optimizer): the optimizer used during the backpropagation step
        config (config.Config): Values for various configuration options
    
    Returns:
        tf.train.CheckpointManager, tf.train.Ckeckpoint
    """
    
    ckpt = Checkpoint(encoder = model.encoder,
                      decoder = model.decoder,
                      optimizer = optimizer)
    ckpt_manager = CheckpointManager(ckpt, checkpoints_dir, max_to_keep=max_checkpoints)

    return ckpt_manager, ckpt

@tf.function
def train_step(model, img_tensor, target, optimizer, loss_function):
    """Forward propagation step.

    Args:
        model (mode.ImageCaptionModel): object containing encoder, decoder and tokenizer
        img_tensor (tensor): Tensor made of image features, with shape = (batch_size, feature_size, num_features).
            feature_size and num_features depend on the CNN used for the encoder, for example with Inception-V3
            the image features are 8x8x2048, which results in a shape of  (batch_size, 64, 20148).
        target (tensor): tokenized captions, shape = (batch_size, max_captions_length).
            max_captions_length depends on the dataset being used, 
            for example, in COCO 2014 dataset max_captions_length = 53.
        optimizer (tf.optimizers.Optimizer): the optimizer used during the backpropagation step.
        loss_function (tf.losses.Loss): Object that computes the loss function.
            Actually only the SparseCategorialCrossentry is supported
        batch_size (integer): Predefined batch size
    
    Returns:
        loss: loss value for all the 
        total_loss: loss value averaged by the size of captions ()
    """

    encoder = model.encoder
    decoder = model.decoder
    tokenizer = model.tokenizer
    loss = 0

    # obtain the actual, real batch size for this batch. 
    # it may differ from predefined batchsize when running the last batch of an epoch
    actual_batch_size=target.shape[0]
    sequence_length=target.shape[1]

    # initializing the hidden state for each batch
    # because the captions are not related from image to image
    hidden = decoder.reset_state(batch_size=actual_batch_size)

    dec_input = tf.expand_dims([tokenizer.word_index['<start>']] * actual_batch_size, 1)

    with tf.GradientTape() as tape:
        features = encoder(img_tensor)
        for i in range(1, sequence_length):

            # passing the features through the decoder
            predictions, hidden, _ = decoder(dec_input, features, hidden)
            loss += compute_loss(target[:, i], predictions, loss_function)
            # using teacher forcing
            dec_input = tf.expand_dims(target[:, i], 1)

    total_loss = (loss / int(sequence_length))
    trainable_variables = encoder.trainable_variables + decoder.trainable_variables
    gradients = tape.gradient(loss, trainable_variables)
    optimizer.apply_gradients(zip(gradients, trainable_variables))

    return loss, total_loss


def fit(model, train_dataset, config):
    """Fits the model for the given dataset
    
    Arguments:
        model {models.ImageCaptionModel} -- The full image captioning model
        train_dataset {dataset.DataSet} -- Container for the dataset and related info
        config (util.Config): Values for various configuration options
    
    Returns:
        list -- List of losses per batch of training
    """
    dataset = train_dataset.dataset
    num_examples = train_dataset.num_instances
    batch_size = train_dataset.batch_size
    num_batches = train_dataset.num_batches
    num_epochs = config.num_epochs
    optimizer = tf.optimizers.get(config.optimizer)
    loss_function = SparseCategoricalCrossentropy(from_logits=True, reduction='none')

    logging.info("Training on %d examples for %d epochs", num_examples, num_epochs)
    logging.info("Divided into %d batches of size %d", num_batches, batch_size)

    resume_training = False
    if config.resume_from_checkpoint:
        ckpt_manager, ckpt = get_checkpoint_manager(model, optimizer, config.checkpoints_dir, config.max_checkpoints)
        status = ckpt.restore(ckpt_manager.latest_checkpoint)
        if ckpt_manager.latest_checkpoint:
            # assert_consumed() raises an error because of delayed restoration 
            # See https://www.tensorflow.org/alpha/guide/checkpoints#delayed_restorations
            # status.assert_consumed() 
            status.assert_existing_objects_matched()
            resume_training = True
    
    if resume_training:
        start_epoch = int(ckpt_manager.latest_checkpoint.split('-')[-1])
        logging.info("Resuming training from epoch %d", start_epoch) 
    else:
        start_epoch = 0
        logging.info("Starting training from scratch")

    batch_losses = []

    for epoch in range(start_epoch, num_epochs):
        start = time.time()
        total_loss = 0
        
        # training steps for one epoch
        for (batch, (img_tensor, target)) in enumerate(dataset):
            batch_loss, t_loss = train_step(model, img_tensor, target, optimizer, loss_function)
            total_loss += t_loss

            if batch % 100 == 0:
                caption_length = int(target.shape[1])
                logging.info('Epoch %d Batch %d/%d Loss: %.4f',
                    epoch + 1, batch, num_batches, batch_loss.numpy() / caption_length)
        # storing the epoch end loss value to plot later
        batch_losses.append(total_loss / num_batches)

        # if epoch % 5 == 0:
        #     ckpt_manager.save()
        logging.info ('Epoch %d Loss %.6f', epoch + 1, total_loss / num_batches)
        logging.info ('Time taken for 1 epoch: %d sec\n', time.time() - start)
        ckpt_manager.save()

    return batch_losses

def train(config):
    """Orchestrates the training process.
    
    This method is responsible of executing all the steps required to train a new model, 
    which includes:
    - Preparing the dataset
    - Building the model
    - Fitting the model to the data

    Arguments:
        config (util.Config): Values for various configuration options
    """
    train_dataset = prepare_train_data(config)
    tokenizer = train_dataset.tokenizer
    model = build_model(tokenizer, config)
    start = time.time()
    losses = fit(model, train_dataset, config)
    logging.info('Total training time: %d seconds', time.time() - start)
    logging.info ('Final loss after %d epochs = %.6f', config.num_epochs, losses[-1])
    plot_loss(losses)