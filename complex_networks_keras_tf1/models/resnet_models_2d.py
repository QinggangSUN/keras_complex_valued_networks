# -*- coding: utf-8 -*-

#  Authors: Qinggang Sun
#
#  Reference:
#       Allen Goodman, Allen Goodman, Claire McQuin, Hans Gaiser, et al. keras-resnet
#       https://github.com/broadinstitute/keras-resnet

import keras
import keras.backend as K
from ..layers.activations import layer_activation
from ..layers.conv import ComplexConv2D
from ..layers.dense import ComplexDense
from ..layers.bn import ComplexBatchNormalization
from ..layers.pool import SpectralPooling2D, ComplexMaxPooling2D, ComplexAveragePooling2D
from .resnet_blocks_2d import basic_2d, bottleneck_2d

class ResNet2D(keras.Model):
    """
    Constructs a `keras.models.Model` object using the given block count.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:
        >>> from .resnet_blocks_2d import block_func
        >>> from keras.layers import Input
        >>> num_blocks = [2, 2, 2, 2]
        >>> block_func = block_func
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D
        >>> model = ResNet2D(inputs, classes=od,
                             pooling_func=['max','global_average'],
                             output_activation='sigmoid')
        >>> print(model.summary())
    """
    def __init__(
        self,
        inputs,
        num_blocks,
        block_func,
        activation='crelu',
        n_filters=64,
        pooling_func=['max', 'global_average'],
        include_top=True,
        classes=1000,
        numerical_names=None,
        output_activation=None,
        *args,
        **kwargs
    ):
        axis = -1 if keras.backend.image_data_format() == "channels_last" else 1

        if numerical_names is None:
            numerical_names = [True] * len(num_blocks)

        x_complex = ComplexConv2D(n_filters, 7, strides=(2, 2), padding='same', use_bias=False, spectral_parametrization=False,
                                  name='conv1')(inputs)

        x_complex = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name='bn_conv1')(x_complex)

        x_complex = layer_activation(x_complex, activation, name=f'conv1_{activation}')

        if pooling_func[0] == 'max':
            x_complex = ComplexMaxPooling2D(pool_size=(3, 3), strides=(2, 2), padding='same', name='pool1')(x_complex)
        elif pooling_func[0] == 'average':
            x_complex = ComplexAveragePooling2D(pool_size=(3, 3), strides=(2, 2), padding='same', name='pool1')(x_complex)

        outputs = []

        for stage_id, iterations in enumerate(num_blocks):
            for block_id in range(iterations):
                x_complex = block_func(
                    n_filters,
                    stage_id,
                    block_id,
                    numerical_name=(block_id > 0 and numerical_names[stage_id]),
                    activation=activation
                )(x_complex)

            n_filters *= 2

            outputs.append(x_complex)

        if include_top:
            assert classes > 0
            if pooling_func[1] == 'global_average':
                x_complex = keras.layers.GlobalAveragePooling2D(name="pool5")(x_complex)
            elif pooling_func[1] == 'complex_average':
                x_complex = ComplexAveragePooling2D(name='pool5')(x_complex)
            elif pooling_func[1] == 'complex_max':
                x_complex = ComplexMaxPooling2D(name='pool5')(x_complex)
            elif pooling_func[1] == 'spectral_average':
                x_complex = SpectralPooling2D(gamma=[0.25, 0.25], name='pool5')(x_complex)

            if output_activation is None:
                output_activation = 'softmax'

            if K.ndim(x_complex) > 2:
                x_complex = keras.layers.Flatten()(x_complex)

            if output_activation.startswith('complex_'):
                output_activation = output_activation[len('complex_'):]
                x = ComplexDense(classes, activation=output_activation, name=f'fc{classes}')(x_complex)
            else:
                x = keras.layers.Dense(classes, activation=output_activation, name=f'fc{classes}')(x_complex)

            super(ResNet2D, self).__init__(inputs=inputs, outputs=x, *args, **kwargs)
        else:
            # Else output each stages features
            super(ResNet2D, self).__init__(inputs=inputs, outputs=outputs, *args, **kwargs)

class ResNet2D18(ResNet2D):
    """
    Constructs a `keras.models.Model` according to the ResNet18 specifications.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D18
        >>> from keras.layers import Input
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> model_resnet = ResNet2D18(inputs, classes=od,
                                      pooling_func=['max','global_average'],
                                      output_activation='sigmoid')
        >>> print(model_resnet.summary())
    """


    def __init__(
            self,
            inputs,
            num_blocks=None,
            block_func=basic_2d,
            conv_activation='crelu',
            n_filters=64,
            pooling_func=['max', 'global_average'],
            include_top=True,
            classes=1000,
            numerical_names=None,
            output_activation='sigmoid',
            *args,
            **kwargs):

        if num_blocks is None:
            num_blocks = [2, 2, 2, 2]

        super(ResNet2D18, self).__init__(
            inputs,
            num_blocks,
            block_func,
            conv_activation,
            n_filters,
            pooling_func,
            include_top,
            classes,
            numerical_names,
            output_activation,
            *args,
            **kwargs
        )

class ResNet2D34(ResNet2D):
    """
    Constructs a `keras.models.Model` according to the ResNet34 specifications.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D34
        >>> from keras.layers import Input
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> model_resnet = ResNet2D34(inputs, classes=od,
                                      pooling_func=['max','global_average'],
                                      output_activation='sigmoid')
        >>> print(model_resnet.summary())
    """


    def __init__(
            self,
            inputs,
            num_blocks=None,
            block_func=basic_2d,
            conv_activation='crelu',
            n_filters=64,
            pooling_func=['max', 'global_average'],
            include_top=True,
            classes=1000,
            numerical_names=None,
            output_activation='sigmoid',
            *args,
            **kwargs):

        if num_blocks is None:
            num_blocks = [3, 4, 6, 3]

        super(ResNet2D34, self).__init__(
            inputs,
            num_blocks,
            block_func,
            conv_activation,
            n_filters,
            pooling_func,
            include_top,
            classes,
            numerical_names,
            output_activation,
            *args,
            **kwargs
        )

class ResNet2D50(ResNet2D):
    """
    Constructs a `keras.models.Model` according to the ResNet50 specifications.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D50
        >>> from keras.layers import Input
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> model_resnet = ResNet2D50(inputs, classes=od,
                                      pooling_func=['max','global_average'],
                                      output_activation='sigmoid')
        >>> print(model_resnet.summary())
    """


    def __init__(
            self,
            inputs,
            num_blocks=None,
            block_func=bottleneck_2d,
            conv_activation='crelu',
            n_filters=64,
            pooling_func=['max', 'global_average'],
            include_top=True,
            classes=1000,
            numerical_names=None,
            output_activation='sigmoid',
            *args,
            **kwargs):

        if num_blocks is None:
            num_blocks = [3, 4, 6, 3]

        numerical_names = [False, False, False, False]

        super(ResNet2D50, self).__init__(
            inputs,
            num_blocks,
            block_func,
            conv_activation,
            n_filters,
            pooling_func,
            include_top,
            classes,
            numerical_names,
            output_activation,
            *args,
            **kwargs
        )

class ResNet2D101(ResNet2D):
    """
    Constructs a `keras.models.Model` according to the ResNet101 specifications.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D101
        >>> from keras.layers import Input
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> model_resnet = ResNet2D101(inputs, classes=od,
                                      pooling_func=['max','global_average'],
                                      output_activation='sigmoid')
        >>> print(model_resnet.summary())
    """


    def __init__(
            self,
            inputs,
            num_blocks=None,
            block_func=bottleneck_2d,
            conv_activation='crelu',
            n_filters=64,
            pooling_func=['max', 'global_average'],
            include_top=True,
            classes=1000,
            numerical_names=None,
            output_activation='sigmoid',
            *args,
            **kwargs):

        if num_blocks is None:
            num_blocks = [3, 4, 23, 3]

        numerical_names = [False, True, True, False]

        super(ResNet2D101, self).__init__(
            inputs,
            num_blocks,
            block_func,
            conv_activation,
            n_filters,
            pooling_func,
            include_top,
            classes,
            numerical_names,
            output_activation,
            *args,
            **kwargs
        )

class ResNet2D152(ResNet2D):
    """
    Constructs a `keras.models.Model` according to the ResNet152 specifications.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D152
        >>> from keras.layers import Input
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> model_resnet = ResNet2D152(inputs, classes=od,
                                      pooling_func=['max','global_average'],
                                      output_activation='sigmoid')
        >>> print(model_resnet.summary())
    """


    def __init__(
            self,
            inputs,
            num_blocks=None,
            block_func=bottleneck_2d,
            conv_activation='crelu',
            n_filters=64,
            pooling_func=['max', 'global_average'],
            include_top=True,
            classes=1000,
            numerical_names=None,
            output_activation='sigmoid',
            *args,
            **kwargs):

        if num_blocks is None:
            num_blocks = [3, 8, 36, 3]

        numerical_names = [False, True, True, False]

        super(ResNet2D152, self).__init__(
            inputs,
            num_blocks,
            block_func,
            conv_activation,
            n_filters,
            pooling_func,
            include_top,
            classes,
            numerical_names,
            output_activation,
            *args,
            **kwargs
        )

class ResNet2D200(ResNet2D):
    """
    Constructs a `keras.models.Model` according to the ResNet200 specifications.

    :param inputs: input tensor (e.g. an instance of `keras.layers.Input`)

    :param num_blocks: list, number of residual blocks

    :param block_func: method, the network’s residual architecture

    :param conv_activation: str, the activation of convolution layer in residual blocks

    :param n_filters: int, the number of filters of the first convolution layer in  residual blocks

    :param pooling_func: list, the type of pooling layers in network

    :param include_top: bool, if true, includes classification layers

    :param classes: int, number of classes to classify (include_top must be true)

    :param output_activation: int, activation of the output Dense layer of the classifer

    :return model: ResNet model with encoding output (if `include_top=False`) or classification output (if `include_top=True`)

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_2d import ResNet2D200
        >>> from keras.layers import Input
        >>> id1, id2, od = 128, 128, 3
        >>> inputs = Input(shape=(id1, id2, 2))
        >>> model_resnet = ResNet2D200(inputs, classes=od,
                                      pooling_func=['max','global_average'],
                                      output_activation='sigmoid')
        >>> print(model_resnet.summary())
    """


    def __init__(
            self,
            inputs,
            num_blocks=None,
            block_func=bottleneck_2d,
            conv_activation='crelu',
            n_filters=64,
            pooling_func=['max', 'global_average'],
            include_top=True,
            classes=1000,
            numerical_names=None,
            output_activation='sigmoid',
            *args,
            **kwargs):

        if num_blocks is None:
            num_blocks = [3, 24, 36, 3]

        numerical_names = [False, True, True, False]

        super(ResNet2D200, self).__init__(
            inputs,
            num_blocks,
            block_func,
            conv_activation,
            n_filters,
            pooling_func,
            include_top,
            classes,
            numerical_names,
            output_activation,
            *args,
            **kwargs
        )

