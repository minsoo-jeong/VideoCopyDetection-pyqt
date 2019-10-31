from torchsummary import summary
from torch.nn import functional as F
from torchvision.datasets.folder import default_loader
from torchvision.transforms import transforms as trn
from torch.utils.data import DataLoader, Dataset
import torch
import os
import sys

from VideoCopyDetector.models import DummyEmb

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))

from .TemporalNetwork import TN
from .Period import *
from utils import *

#preSampled = 'D:/VCDB_presampled/'
preSampled = 'E:/VCDB_presampled/'

def cosine_similarity_auto(query, features, cuda=True, numpy=True, query_split_cnt=200):
    score, idx, cos = cosine_similarity(query, features, cuda=cuda, numpy=numpy) \
        if query.shape[0] < query_split_cnt else cosine_similarity_split(query, features, cuda=cuda, numpy=numpy)
    return score, idx, cos


# multiple query
def cosine_similarity(query, features, cuda=True, numpy=True):
    if cuda:
        query = query.cuda()
        features = features.cuda()
    query = F.normalize(query, 2, 1)
    features = F.normalize(features, 2, 1)

    cos = torch.mm(features, query.t()).t()
    score, idx = torch.sort(cos, descending=True)

    post = lambda x: x.cpu().numpy() if numpy else x.cpu()

    score, idx, cos = map(post, [score, idx, cos])

    return score, idx, cos


def cosine_similarity_split(query, features, cuda=True, numpy=True):
    toCPU = lambda x: x.cpu()
    toNumpy = lambda x: x.numpy()
    q_l = query.split(100, dim=0)
    score_l = []
    cos_l = []
    idx_l = []
    if cuda:
        features = features.cuda()
    for q in q_l:
        if cuda: q = q.cuda()
        q = F.normalize(q, 2, 1)
        features = F.normalize(features, 2, 1)
        cos = torch.mm(features, q.t()).t()
        score, idx = torch.sort(cos, descending=True)
        score, idx, cos = map(toCPU, [score, idx, cos])

        cos_l.append(cos)
        score_l.append(score)
        idx_l.append(idx)

    cos = torch.cat(cos_l, dim=0)
    score = torch.cat(score_l, dim=0)
    idx = torch.cat(idx_l, dim=0)
    score, idx, cos = map(toNumpy, [score, idx, cos])

    return score, idx, cos


class ListDataset(Dataset):
    def __init__(self, l):
        self.l = l
        self.loader = default_loader
        self.default_trn = trn.Compose([
            trn.Resize((224, 224)),
            trn.ToTensor(),
            trn.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

    def __getitem__(self, idx):
        path = self.l[idx]
        frame = self.default_trn(self.loader(path))

        return path, frame

    def __len__(self):
        return len(self.l)


class Detector:
    def __init__(self, cuda):
        self.model = DummyEmb()
        self.cuda = cuda
        if self.cuda:
            self.model.cuda()
        self.model.eval()

        self.listLoader = DataLoader(ListDataset([]), batch_size=128, shuffle=False, num_workers=4)

    def Extract_FingerPrint(self, frameList):
        self.model.eval()
        with torch.no_grad():
            self.listLoader.dataset.l = frameList
            fingerprint = []
            for chunck_idx, (paths, frames) in enumerate(self.listLoader):
                if self.cuda:
                    frames = frames.cuda()
                out = self.model(frames)

                fingerprint.append(out.cpu())
        fingerprint = torch.cat(fingerprint)
        print('[Extract Query Fp] {}'.format(fingerprint.shape))
        return fingerprint

    def LoadRefeneceFeautre(self, fps, ref_video):
        ref_videos_fingerprint = []
        ref_videos_names = []
        ref_videos_delimter = [0]

        print('',end=' ')
        featureBase = os.path.join(preSampled, 'FPS_{}'.format(fps))  # title/name
        for n, (name, dt, title, fps, duration, count) in enumerate(ref_video):
            path = os.path.join(featureBase, title, os.path.splitext(name)[0] + '.pt')
            f = torch.load(path)
            ref_videos_fingerprint.append(f.cpu())
            ref_videos_names.append((title,name))
            ref_videos_delimter.append(ref_videos_delimter[-1] + f.shape[0])
            if n%100==0:
                print('\r[Load Ref Fp] count: {:3}'.format(n),end=' ')


        ref_videos_fingerprint = torch.cat(ref_videos_fingerprint)
        ref_videos_delimter = np.array(ref_videos_delimter)
        print('\r[Load Ref Fp] count: {} {}'.format(len(ref_video),ref_videos_fingerprint.shape))

        return ref_videos_fingerprint, ref_videos_delimter, ref_videos_names

    def detect(self, queryDir, offset, fps, ref_video, TOP_K, SCORE_THR, TEMP_WND, MIN_PATH, MIN_MATCH):
        queryList = [os.path.join(queryDir, i) for i in os.listdir(queryDir)]

        query = self.Extract_FingerPrint(queryList)
        ref_videos_fingerprint, ref_videos_delimter, ref_videos_names = self.LoadRefeneceFeautre(fps, ref_video)

        score, idx, cos = cosine_similarity_auto(query, ref_videos_fingerprint, cuda=True, numpy=True)

        tn = TN(score, idx, ref_videos_delimter, TOP_K=TOP_K, SCORE_THR=SCORE_THR,
                TEMP_WND=TEMP_WND, MIN_PATH=MIN_PATH, MIN_MATCH=MIN_MATCH)
        result = tn.fit()


        result = [{'query': Period(offset + (p['query'].start / fps),
                                   offset + (p['query'].end / fps)),
                   'ref_title':ref_videos_names[p['ref_vid_idx']][0],
                   'ref_name': ref_videos_names[p['ref_vid_idx']][1],
                   'ref': Period((p['ref'].start - ref_videos_delimter[p['ref_vid_idx']]) / fps,
                                 (p['ref'].end - ref_videos_delimter[p['ref_vid_idx']]) / fps),
                   'score': p['score']} for p in result]
        print(result)
        return result


if __name__ == '__main__':
    import sys
    from App import MyApp

    app = QApplication(sys.argv)
    ex = MyApp()
    ex.show()
    sys.exit(app.exec_())
