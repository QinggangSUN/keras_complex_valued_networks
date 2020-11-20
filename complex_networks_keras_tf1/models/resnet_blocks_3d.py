# -*- coding: utf-8 -*-

"""
This module implements a number of popular two-dimensional complex valued residual blocks.
"""

#  Authors: Qinggang Sun
#
#  Reference:
#       Allen Goodman, Allen Goodman, Claire McQuin, Hans Gaiser, et al. keras-resnet
#       https://github.com/broadinstitute/keras-resnet

from ..layers.activations import layer_activation
from ..layers.bn import ComplexBatchNormalization
from ..layers.conv import ComplexConv3D

import keras.layers
import keras.regularizers

def basic_3d(
    filters,
    stage=0,
    block=0,
    kernel_size=3,
    numerical_name=False,
    stride=None,
    activation='crelu',
    **kwargs,
):
    """
    A two-dimensional basic block.

    :param filters: int, the output’s feature space

    :param stage: int, representing the stage of this block (starting from 0)

    :param block: int, representing this block (starting from 0)

    :param kernel_size: int or tuple/list of 2 integers, size of the kernel

    :param numerical_name: bool, if true, uses numbers to represent blocks instead of chars (ResNet{18, 34})

    :param stride: int, representing the stride used in the shortcut and the first conv layer, default derives stride from block id

    :param activation: str, the activation of convolution layer in residual blocks

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_3d import basic_3d

        >>> basic_3d(64)
    """
    if stride is None:
        if block != 0 or stage == 0:
            stride = 1
        else:
            stride = 2

    axis = -1 if keras.backend.image_data_format() == "channels_last" else 1

    if block > 0 and numerical_name:
        block_char = f'b{block}'
    else:
        block_char = chr(ord('a') + block)

    stage_char = str(stage + 2)

    def f(inputs, **kwargs):
        outputs = keras.layers.ZeroPadding3D(padding=1, name=f'padding{stage_char}{block_char}_branch2a')(inputs)

        outputs = ComplexConv3D(filters, kernel_size, strides=stride, use_bias=False, spectral_parametrization=False,
                                name=f'res{stage_char}{block_char}_branch2a', **kwargs)(outputs)

        outputs = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch2a')(outputs)

        outputs = layer_activation(outputs, activation, name=f'res{stage_char}{block_char}_branch2a_{activation}')

        outputs = keras.layers.ZeroPadding3D(padding=1, name=f'padding{stage_char}{block_char}_branch2b')(outputs)

        outputs = ComplexConv3D(filters, kernel_size, use_bias=False, spectral_parametrization=False,
                                name=f'res{stage_char}{block_char}_branch2b', **kwargs)(outputs)

        outputs = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch2b')(outputs)

        if block == 0:
            shortcut = ComplexConv3D(filters, (1, 1), strides=stride, use_bias=False, spectral_parametrization=False,
                                     name=f'res{stage_char}{block_char}_branch1', **kwargs)(inputs)

            shortcut = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch1')(shortcut)
        else:
            shortcut = inputs

        outputs = keras.layers.add([outputs, shortcut], name=f'res{stage_char}{block_char}')

        outputs = layer_activation(outputs, activation, name=f'res{stage_char}{block_char}_{activation}')

        return outputs

    return f


def bottleneck_3d(
    filters,
    stage=0,
    block=0,
    kernel_size=3,
    numerical_name=False,
    stride=None,
    activation='crelu',
    **kwargs,
):
    """
    A two-dimensional bottleneck block.

    :param filters: int, the output’s feature space

    :param stage: int, representing the stage of this block (starting from 0)

    :param block: int, representing this block (starting from 0)

    :param kernel_size: int or tuple/list of 2 integers, size of the kernel

    :param numerical_name: bool, if true, uses numbers to represent blocks instead of chars (ResNet{101, 152, 200})

    :param stride: int, representing the stride used in the shortcut and the first conv layer, default derives stride from block id

    :param activation: str, the activation of convolution layer in residual blocks

    Usage:

        >>> from complex_networks_keras_tf1.models.resnet_models_3d import bottleneck_3d

        >>> bottleneck_3d(64)
    """

    if stride is None:
        if block != 0 or stage == 0:
            stride = 1
        else:
            stride = 2

    axis = -1 if keras.backend.image_data_format() == "channels_last" else 1

    if block > 0 and numerical_name:
        block_char = f'b{block}'
    else:
        block_char = chr(ord('a') + block)

    stage_char = str(stage + 2)

    def f(inputs, **kwargs):
        outputs = ComplexConv3D(filters, 1, strides=stride, use_bias=False, spectral_parametrization=False,
                                name=f'res{stage_char}{block_char}_branch2a', **kwargs)(inputs)

        outputs = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch2a')(outputs)

        outputs = layer_activation(outputs, activation, name=f'res{stage_char}{block_char}_branch2a_{activation}')

        outputs = keras.layers.ZeroPadding3D(padding=1, name=f'padding{stage_char}{block_char}_branch2b')(outputs)

        outputs = ComplexConv3D(filters, kernel_size, use_bias=False, spectral_parametrization=False,
                                name=f'res{stage_char}{block_char}_branch2b', **kwargs)(outputs)

        outputs = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch2b')(outputs)

        outputs = layer_activation(outputs, activation, name=f'res{stage_char}{block_char}_branch2b_{activation}')

        outputs = ComplexConv3D(filters*4, 1, strides=(1, 1), use_bias=False, spectral_parametrization=False,
                                name=f'res{stage_char}{block_char}_branch2c', **kwargs)(outputs)

        outputs = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch2c')(outputs)

        if block == 0:
            shortcut = ComplexConv3D(filters*4, (1, 1), strides=stride, use_bias=False, spectral_parametrization=False,
                                     name=f'res{stage_char}{block_char}_branch1', **kwargs)(inputs)

            shortcut = ComplexBatchNormalization(axis=axis, epsilon=1e-5, name=f'bn{stage_char}{block_char}_branch1')(shortcut)
        else:
            shortcut = inputs

        outputs = keras.layers.add([outputs, shortcut], name=f'res{stage_char}{block_char}')

        outputs = layer_activation(outputs, activation, name=f'res{stage_char}{block_char}_{activation}')

        return outputs

    return f
