import os
os.environ['KERAS_BACKEND'] = 'theano'
os.environ['THEANO_FLAGS'] = 'floatX=float32,device=cpu'

import pandas as pd
import numpy as np
import json
import logging

from keras_theano_model import KerasTheanoModel
from pipeline_monitor import prometheus_monitor as monitor
from pipeline_logger import log

_logger = logging.getLogger('model_logger')
_logger.setLevel(logging.INFO)
_logger_stream_handler = logging.StreamHandler()
_logger_stream_handler.setLevel(logging.INFO)
_logger.addHandler(_logger_stream_handler)


__all__ = ['predict']


_labels= {'model_type': os.environ['PIPELINE_MODEL_TYPE'],
          'model_name': os.environ['PIPELINE_MODEL_NAME'],
          'model_tag': os.environ['PIPELINE_MODEL_TAG']}


def _initialize_upon_import(model_state_path: str) -> KerasTheanoModel:
    ''' Initialize / Restore Model Object.
    '''
    return KerasTheanoModel(model_state_path)


# This is called unconditionally at *module import time*...
_model = _initialize_upon_import(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'state/keras_theano_linear_model_state.h5'))

@monitor(labels=_labels, name="transform_request")
def _json_to_numpy(request: bytes) -> np.array:
    request_str = request.decode('utf-8')
    request_str = request_str.strip().replace('\n', ',')
    # surround the json with '[' ']' to prepare for conversion
    request_str = '[%s]' % request_str
    request_json = json.loads(request_str)
    request_transformed = ([json_line['ppt'] for json_line in request_json])
    return np.array(request_transformed)


@monitor(labels=_labels, name="transform_response")
def _numpy_to_json(response: np.array) -> bytes:
    return json.dumps(response.tolist())


@log(labels=_labels, logger=_logger)
def predict(request: bytes) -> bytes:
    '''Where the magic happens...'''
    transformed_request = _json_to_numpy(request)

    with monitor(labels=_labels, name="predict"):
        predictions = _model.predict(transformed_request)

    return _numpy_to_json(predictions)
