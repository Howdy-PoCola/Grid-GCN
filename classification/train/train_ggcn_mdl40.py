import mxnet as mx
import logging
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../..'))
print(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from configs.configs import configs
from models.ggcn_models import get_symbol_cls_ggcn, get_symbol_cls_fps_gcn
from data_loader.ggcn_modelnet40_loader import ModelNet40Loader as loader
from train.base_solver import BaseSolver
from utils import metrics

class ModelNet40Solver(BaseSolver):
    def __init__(self):
        super(ModelNet40Solver, self).__init__()

    def _specify_input_names(self, layer_num=None):
        if layer_num is None:
            layer_num = len(configs['voxel_size_lst'])

        self.data_names = ['data']
        self.label_names = ['label']
        if not configs["fps"]:
            for i in range(layer_num):
                if configs["agg"] in ["max","max_pooling"]:
                    self.data_names += ['neighbors_arr'+str(i),
                                        'centers_arr'+str(i),
                                        'centers_mask'+str(i)]
                else:
                    self.data_names += ['neighbors_arr'+str(i),
                                        'neighbors_mask' + str(i),
                                        'centers_arr'+str(i),
                                        'centers_mask'+str(i)]

    def _get_symbol(self):
        take_shapes = []
        for i in range(len(configs['voxel_size_lst'])):
            take_shapes.append([self.batch_size, configs['max_o_grid_lst'][i],
                configs['max_p_grid_lst'][i],  configs['num_points'] if i == 0 else configs['max_o_grid_lst'][i-1],
                configs['inputDim'][i]])
            # print("take_shapes {}/{}".format(i, take_shapes[i]))
        if configs['task'] == 'cls':
            if configs['fps']:
                self.symbol = get_symbol_cls_fps_gcn(self.batch_size/self.num_devices, self.num_points,
                    take_shapes, gcn_outDim=configs['gcn_outDim'], bn_decay=self.bn_decay, weights=self.weights)
            else:
                self.symbol = get_symbol_cls_ggcn(self.batch_size/self.num_devices, self.num_points,
                    take_shapes, gcn_outDim=configs['gcn_outDim'], bn_decay=self.bn_decay, weights=self.weights)
        else:
            raise NotImplementedError("Task not identified")

    def _get_data_loaders(self):
        self.train_loader = loader(
            root=configs['data_dir'],
            batch_size=self.batch_size,
            npoints=self.num_points,
            normal_channel=configs['use_normal'],
            split='train',
            augment_level=configs['augment_level'],
            shuffle=True,
            balance=False,
            dropout_ratio=configs['input_dropout_ratio'],
            voxel_size_lst=configs['voxel_size_lst'], grid_size_lst=configs['grid_size_lst'],
            lidar_coord=configs['lidar_coord'], max_p_grid_lst=configs['max_p_grid_lst'],
            max_o_grid_lst=configs['max_o_grid_lst'], kernel_size_lst=configs['kernel_size_lst'],
            stride_lst=configs['stride_lst'], single_padding_lst=configs['single_padding_lst'],
            reverse_index=configs['reverse_index']
        )


        self.val_loader = loader(
            root=configs['data_dir'],
            batch_size=self.batch_size,
            npoints=self.num_points,
            normal_channel=configs['use_normal'],
            split='test',
            dropout_ratio=0,
            voxel_size_lst=configs['voxel_size_lst'], grid_size_lst=configs['grid_size_lst'],
            lidar_coord=configs['lidar_coord'], max_p_grid_lst=configs['max_p_grid_lst'],
            max_o_grid_lst=configs['max_o_grid_lst'], kernel_size_lst=configs['kernel_size_lst'],
            stride_lst=configs['stride_lst'], single_padding_lst=configs['single_padding_lst'],
            reverse_index=configs['reverse_index']
        )

    def _get_metric(self):
        self.metric = mx.metric.CompositeEvalMetric([mx.metric.Accuracy(), mx.metric.CrossEntropy()])

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    solver = ModelNet40Solver()
    solver.train()


