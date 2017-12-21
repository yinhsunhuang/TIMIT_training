import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader
from torch.utils.data.sampler import Sampler
class FbankDataset(Dataset):
    """FbankD Dataset"""
    def __init__(self, base_dir='MLDS_HW1_RELEASE_v1/', is_test=False):
        self._loaded = False
        self._base_dir = base_dir
        self._is_test = is_test
        self.window_len = 11
        
        self.loadMap()
        self.loadData()
        super(FbankDataset, self).__init__()

    def __len__(self):
        return self.N

    def __getitem__(self, idx):
        if not self._is_test:
            sample = {
                'label': self.frame_names[idx],
                'x': self.x[idx:idx+self.window_len,:].flatten(),
                'y': self.y[idx]
            }
        else:
            sample = {
                'label': self.frame_names[idx],
                'x':self.x[idx:idx+self.window_len,:].flatten()
            }
        return sample

    def to_onehot(self,x):
        out = np.zeros(self.y_dim,np.int8)
        out[x]=1
        return out
        
    def loadData(self,ratio=0.1):
        '''Helper function for loading training data and labels'''
        if not self._is_test:
            self.fbank_train = pd.read_csv(self._base_dir + 'fbank/train.ark', index_col=0, sep=' ', header=None)
        else:
            self.fbank_train = pd.read_csv(self._base_dir + 'fbank/test.ark', index_col=0, sep=' ', header=None)
            
        self.frame_names = self.fbank_train.index.tolist()
        self.x = self.fbank_train.values
        self.N = self.x.shape[0]
        self.x_dim = self.x.shape[1]

        self.x = np.vstack( ( np.zeros(((self.window_len-1)//2,self.x.shape[1])), self.x ,np.zeros(((self.window_len-1)//2,self.x.shape[1])) ) )
        
        if not self._is_test:
            self.labels = pd.read_csv(self._base_dir+'state_label/train.lab',index_col=0, sep=',', header=None)
            self.y = self.labels.ix[self.frame_names, :].values
            self.y_dim = 1943
            self.y = np.asarray(self.y,dtype=np.int32)
            #self.y = np.asarray([self.to_onehot(yi) for yi in self.y],dtype=np.uint8)
            #self.y = np.asarray([self.phone_ctr[yi[0]] for yi in self.y],dtype=np.uint8)
            self.y = np.squeeze(self.y)


    def loadMap(self):
        # 48-39 map
        self.phone_map={}
        self.phone_ctr={}
        self.ctr_phone={}
        ctr=0
        with open(self._base_dir+'phones/48_39.map', 'r') as f:
            for l in f:
                ll = l.rstrip().split('\t')
                self.phone_map[ll[0]] = ll[1]
                self.phone_ctr[ll[0]] = ctr
                self.ctr_phone[ctr]=ll[1]
                ctr = ctr + 1

        self.state_39={}
        with open(self._base_dir+'phones/state_48_39.map', 'r') as f:
            for l in f:
                ll = l.rstrip().split('\t')
                self.state_39[int(ll[0])] = ll[2]

class PartialDataset(Dataset):
    def __init__(self, parent_ds, offset, length, perm):
        self.parent_ds = parent_ds
        self.offset = offset
        self.length = length
        self.perm = perm
        assert len(parent_ds)>=offset+length, Exception("Parent Dataset not long enough")
        super(PartialDataset, self).__init__()
    def __len__(self):
        return self.length
    def __getitem__(self, i):
        return self.parent_ds[self.perm[i+self.offset]]

def validation_split(dataset, val_share=0.1):
    val_offset = int(len(dataset)*(1-val_share))
    perm = torch.randperm(len(dataset))
    return PartialDataset(dataset, 0, val_offset, perm), PartialDataset(dataset, val_offset, len(dataset)-val_offset, perm)
