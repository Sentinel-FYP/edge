import tensorflow as tf
from absl import logging


class Model:
    def __init__(self, model_path, clip_length=64, output_size=(172, 172)):
        self.model_path = model_path
        self.clip_length = clip_length
        self.prediction = "Loading..."
        self.frame_count = 0
        logging.set_verbosity(logging.ERROR)
        interpreter = tf.lite.Interpreter(model_path)
        self.model = interpreter.get_signature_runner()
        logging.set_verbosity(logging.INFO)
        self.init_states = self.init_states(interpreter)
        self.states = self.init_states.copy()

    # Extract state names and create the initial (zero) states
    def state_name(self, name: str) -> str:
        return name[len('serving_default_'):-len(':0')]

    def init_states(self, interpreter):
        init_states = {
            self.state_name(x['name']): tf.zeros(x['shape'], dtype=x['dtype'])
            for x in interpreter.get_input_details()
        }
        del init_states['image']
        return init_states

    def feed_frame(self, frame):
        self.frame_count += 1
        inputs = frame[tf.newaxis, tf.newaxis, ...]
        logits, self.states = self.get_logits(inputs)
        if self.frame_count % 64 == 0:
            self.states = self.init_states.copy()
            probabilities = tf.nn.softmax(logits, axis=-1)
            for label, p in self.get_top_k(probabilities[-1]):
                break
            self.prediction = f'{label}: {p:.3f}'

    def get_logits(self, inputs):
        outputs = self.model(**self.states, image=inputs)
        logits = outputs.pop('logits')
        states = outputs
        return logits, states

    def get_top_k(self, probs, k=5, label_map=['Anomaly', 'Normal']):
        """Outputs the top k model labels and probabilities on the given video.

        Args:
        probs: probability tensor of shape (num_frames, num_classes) that represents
            the probability of each class on each frame.
        k: the number of top predictions to select.
        label_map: a list of labels to map logit indices to label strings.

        Returns:
        a tuple of the top-k labels and probabilities.
        """
        # Sort predictions to find top_k
        top_predictions = tf.argsort(
            probs, axis=-1, direction='DESCENDING')[:k]
        # collect the labels of top_k predictions
        top_labels = tf.gather(label_map, top_predictions, axis=-1)
        # decode lablels
        top_labels = [label.decode('utf8') for label in top_labels.numpy()]
        # top_k probabilities of the predictions
        top_probs = tf.gather(probs, top_predictions, axis=-1).numpy()
        return tuple(zip(top_labels, top_probs))
