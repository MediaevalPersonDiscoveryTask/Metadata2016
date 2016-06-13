# Propagate OCR on face clustering

import pandas as pd
import pandas.parser
from pyannote.core import Segment, Annotation
from pyannote.algorithms.tagging.label import ArgMaxTagger
import os
import os.path


REPOSITORY = '/Users/bredin/Development/MediaEval/PersonDiscovery2016Metadata/'

VIDEOS = '{repository}/lists/test.txt'
SHOTS = '{repository}/shots/{uri}.shot'
BASELINE1 = '{repository}/baseline/baseline1/{uri}.txt'
BASELINE2 = '{repository}/baseline/baseline2/{uri}.txt'
BASELINE3 = '{repository}/baseline/baseline3/{uri}.txt'

SUBMISSION = '{repository}/baseline/baseline3_submission.txt'
EVIDENCE = '{repository}/baseline/baseline3_evidence.txt'

EXISTING_EVIDENCE = '{repository}/baseline/baseline2_evidence.txt'

path = VIDEOS.format(repository=REPOSITORY)
names = ['corpus_id', 'video_id']
videos = pd.read_table(path, delim_whitespace=True, header=None, names=names)

TEMPLATE_SUBMISSION = \
    '{corpus_id} {video_id} {shot_id} {person_name} {confidence:.3f}\n'
TEMPLATE_EVIDENCE = \
    '{person_name} {corpus_id} {video_id} {modality} {timestamp:.3f}\n'

evidences = set([])

path_submission = SUBMISSION.format(repository=REPOSITORY)
with open(path_submission, 'w') as fp_submission:

    for _, (corpus_id, video_id) in videos.iterrows():

        uri = corpus_id + '/' + video_id

        names = ['corpus_id', 'video_id', 'shot_id', 'person_name', 'confidence']
        dtype = {'shot_id': str}

        # load baseline 1
        path = BASELINE1.format(repository=REPOSITORY, uri=uri)
        baseline1 = pd.read_table(path, delim_whitespace=True, header=None, names=names, dtype=dtype)
        baseline1 = baseline1.drop(['confidence'], axis=1)

        # load baseline 2
        path = BASELINE2.format(repository=REPOSITORY, uri=uri)
        baseline2 = pd.read_table(path, delim_whitespace=True, header=None, names=names, dtype=dtype)
        baseline2 = baseline2.drop(['confidence'], axis=1)

        # compute intersection
        intersection = baseline1.merge(baseline2)

        path = BASELINE3.format(repository=REPOSITORY, uri=uri)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as fp:

            for _, (corpus_id, video_id, shot_id, person_name) in intersection.iterrows():

                # we need an evidence for this person
                evidences.add(person_name)

                line = TEMPLATE_SUBMISSION.format(
                    corpus_id=corpus_id, video_id=video_id, shot_id=shot_id,
                    person_name=person_name, confidence=1.0)
                fp.write(line)
                fp_submission.write(line)

names = ['person_name', 'corpus_id', 'video_id', 'modality', 'timestamp']
path = EXISTING_EVIDENCE.format(repository=REPOSITORY)
data = pd.read_table(path, delim_whitespace=True, header=None, names=names)

path_evidence = EVIDENCE.format(repository=REPOSITORY)
with open(path_evidence, 'w') as fp_evidence:

    for _, row in data.iterrows():
        evidence = dict(row)
        if not evidence['person_name'] in evidences:
            continue
        line = TEMPLATE_EVIDENCE.format(**evidence)
        fp_evidence.write(line)
