import tensorflow as tf

class MultiLabelMacroRecall(tf.keras.metrics.Metric):
    """Computes the Macro-averaged Recall of the given tensors."""

    def __init__(
        self,
        name:str="multi_label_macro_recall",
        threshold:float=0.5,
        from_logits:bool=True,
        activation:str="sigmoid",
        **kwargs
    ):
        """Creates a `MultiLabelMacroRecall` instance.

        Args:
            name (str): (Optional) string name of the metric instance. Defaults to
                `"multi_label_macro_recall"`.
            threshold (float): (Optional) float value to use to binarize labels and
                predictions. Values greater than `threshold` will set to `1`.
                Defaults to `0.5`.
            from_logits (bool): (Optional) boolean value to specifiy whether or not
                `y_pred` are logits or have not yet been transformed via a final
                activation function. If `from_logits` is `False`, `activation`
                will be applied to `y_pred` prior to metric calculation. Defaults
                to `True`.
            activation (str): (Optional) string value of the activation function
                to apply to `y_pred` if `from_logits=False`. Defaults to `"sigmoid"`
                . Options include `["sigmoid"]`.
        """
        super(MultiLabelMacroRecall, self).__init__(name=name, **kwargs)
        self._threshold = threshold
        self._from_logits = from_logits
        self._activation = activation
        self._recall = self.add_weight(name="mlm_recall", initializer="zeros")

        # NOTE: could be replaced  with tf confusion_matrix utils
        # whether or not the overhead of that is worth is needs to be tested.
        self._true_positives  = self.add_weight(name="tp", initializer="zeros")
        self._false_positives = self.add_weight(name="fp", initializer="zeros")

    def update_state(self, y_true, y_pred, sample_weight=None):
        # apply activation if needed
        y_pred = tf.cond(
            tf.equal(self._from_logits, True),
                lambda: y_pred,
                lambda: tf.cond(
                    tf.equal(self._activation, 'sigmoid'),
                    lambda: tf.sigmoid(y_pred),
                    lambda: y_pred
            )
        )

        # Compare predictions and threshold.
        pred_is_pos = tf.greater(tf.cast(y_pred, tf.float32), self._threshold)
        label_is_pos = tf.greater(tf.cast(y_true, tf.float32), self._threshold)
        label_is_neg = tf.logical_not(tf.cast(label_is_pos, tf.bool))

        self._true_positives.assign_add(
            tf.reduce_sum(
                tf.cast(tf.logical_and(pred_is_pos, label_is_pos), tf.float32)
            )
        )
        self._false_positives.assign_add(
            tf.reduce_sum(
                tf.cast(tf.logical_and(pred_is_pos, label_is_neg), tf.float32)
            )
        )

        tp = self._true_positives
        fp = self._false_positives

        # NOTE: "safe" divide by 0 without NaN this may cause unexpected behavior
        recall = tf.math.divide_no_nan(tp, tf.add(tp, fp))
        self._recall.assign(recall)
        return recall

    def result(self):
        return self._recall

    def reset_states(self):
        # The state of the metric will be reset at the start of each epoch.
        self._recall.assign(0.0)
        self._true_positives.assign(0.0)
        self._false_positives.assign(0.0)


class MultiLabelMacroSpecificity(tf.keras.metrics.Metric):
    """Computes the Macro-averaged Specificity of the given tensors."""

    def __init__(
        self,
        name:str="multi_label_macro_specificity",
        threshold:float=0.5,
        from_logits:bool=True,
        activation:str="sigmoid",
        **kwargs
    ):
        """Creates a `MultiLabelMacroSpecificity` instance.

        Args:
          name (str): (Optional) string name of the metric instance. Defaults to
              `"multi_label_macro_specificity"`.
          threshold (float): (Optional) float value to use to binarize labels and
              predictions. Values greater than `threshold` will set to `1`.
              Defaults to `0.5`.
          from_logits (bool): (Optional) boolean value to specifiy whether or not
              `y_pred` are logits or have not yet been transformed via a final
              activation function. If `from_logits` is `False`, `activation`
              will be applied to `y_pred` prior to metric calculation. Defaults
              to `True`.
          activation (str): (Optional) string value of the activation function
              to apply to `y_pred` if `from_logits=False`. Defaults to `"sigmoid"`
              . Options include `["sigmoid"]`.
        """
        super(MultiLabelMacroSpecificity, self).__init__(name=name, **kwargs)
        self._threshold = tf.constant(threshold)
        self._from_logits = from_logits
        self._activation = activation

        self._specificity = self.add_weight(name="mlm_spec", initializer="zeros")
        # NOTE: could be replaced  with tf confusion_matrix utils
        self._true_negatives = self.add_weight(name="tn", initializer="zeros")
        self._false_positives = self.add_weight(name="fp", initializer="zeros")

    def update_state(self, y_true, y_pred, sample_weight=None):
        # apply activation if needed
        y_pred = tf.cond(
            tf.equal(self._from_logits, True),
            lambda: y_pred,
            lambda: tf.cond(
                tf.equal(self._activation, 'sigmoid'),
                lambda: tf.sigmoid(y_pred),
                lambda: y_pred
            )
        )

        # Compare predictions and threshold.
        pred_is_pos  = tf.greater(tf.cast(y_pred, tf.float32), self._threshold)
        pred_is_neg  = tf.logical_not(tf.cast(pred_is_pos, tf.bool))
        label_is_pos = tf.greater(tf.cast(y_true, tf.float32), self._threshold)
        label_is_neg = tf.logical_not(tf.cast(label_is_pos, tf.bool))

        self._true_negatives.assign_add(
            tf.reduce_sum(
                tf.cast(tf.logical_and(pred_is_neg, label_is_neg), tf.float32)
            )
        )
        self._false_positives.assign_add(
            tf.reduce_sum(
                tf.cast(tf.logical_and(pred_is_pos, label_is_neg), tf.float32)
            )
        )

        tn = self._true_negatives
        fp = self._false_positives
        # NOTE: "safe" divide by 0 without NaN this may cause unexpected behavior
        specificity = tf.math.divide_no_nan(tn, tf.add(tn, fp))
        self._specificity.assign(specificity)
        return specificity

    def result(self):
        return self._specificity


class MultiLabelMacroSensitivity(tf.keras.metrics.Metric):
    """Computes the Macro-averaged Sensitivity of the given tensors."""
    def __init__(
        self,
        name:str='multi_label_macro_sensitivity',
        threshold:float=0.5,
        from_logits:bool=True,
        activation:str='sigmoid',
        **kwargs
    ):
        """Creates a `MultiLabelMacroSensitivity` instance.

        Args:
        name (str): (Optional) string name of the metric instance. Defaults to
            `"multi_label_macro_sensitivity"`.
        threshold (float): (Optional) float value to use to binarize labels and
            predictions. Values greater than `threshold` will set to `1`.
            Defaults to `0.5`.
        from_logits (bool): (Optional) boolean value to specifiy whether or not
            `y_pred` are logits or have not yet been transformed via a final
            activation function. If `from_logits` is `False`, `activation`
            will be applied to `y_pred` prior to metric calculation. Defaults
            to `True`.
        activation (str): (Optional) string value of the activation function
            to apply to `y_pred` if `from_logits=False`. Defaults to `"sigmoid"`
            . Options include `["sigmoid"]`.
        """
        super(MultiLabelMacroSensitivity, self).__init__(name=name, **kwargs)
        self._threshold = tf.constant(threshold)
        self._from_logits = from_logits
        self._activation = activation

        self._sensitivity = self.add_weight(name="mlm_sens", initializer="zeros")
        # NOTE: could be replaced  with tf confusion_matrix utils
        self._true_positives  = self.add_weight(name="tp", initializer="zeros")
        self._false_negatives = self.add_weight(name="fn", initializer="zeros")

    def update_state(self, y_true, y_pred, sample_weight=None):
        # apply activation if needed
        y_pred = tf.cond(
            tf.equal(self.from_logits, True),
            lambda: y_pred,
            lambda: tf.cond(
                tf.equal(self.activation, 'sigmoid'),
                lambda: tf.sigmoid(y_pred),
                lambda: y_pred
            )
        )

        # Compare predictions and threshold.
        pred_is_pos  = tf.greater(tf.cast(y_pred, tf.float32), self._threshold)
        label_is_pos = tf.greater(tf.cast(y_true, tf.float32), self._threshold)

        pred_is_neg  = tf.logical_not(tf.cast(pred_is_pos, tf.bool))
        label_is_neg = tf.logical_not(tf.cast(label_is_pos, tf.bool))

        self._true_positives.assign_add(
            tf.reduce_sum(
                tf.cast(tf.logical_and(pred_is_pos, label_is_pos), tf.float32)
            )
        )
        self._false_negatives.assign_add(
            tf.reduce_sum(
                tf.cast(tf.logical_and(pred_is_neg, label_is_pos), tf.float32)
            )
        )

        tp = self._true_positives
        fn = self._false_negatives
        # NOTE: "safe" divide by 0 without NaN this may cause unexpected behavior
        sensitivity = tf.math.divide_no_nan(tp, tf.add(tp, fn))
        self._sensitivity.assign(sensitivity)
        return sensitivity

    def result(self):
        return self._sensitivity
