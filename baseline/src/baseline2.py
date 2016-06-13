# Propagate OCR on face clustering

import pandas as pd
import pandas.parser
from pyannote.core import Segment, Annotation
from pyannote.algorithms.tagging.label import ArgMaxTagger
import os
import os.path
import itertools


REPOSITORY = '/Users/bredin/Development/MediaEval/PersonDiscovery2016Metadata/'

VIDEOS = '{repository}/lists/test.txt'
SHOTS = '{repository}/shots/{uri}.shot'
OCR = '{repository}/optical_character_recognition/{uri}.txt'
FACE_TRACKING = '{repository}/face_tracking/{uri}.txt'
FACE_CLUSTERING = '{repository}/face_clustering/{uri}.txt'
FUSION = '{repository}/baseline/baseline2/{uri}.txt'
SUBMISSION = '{repository}/baseline/baseline2_submission.txt'
EVIDENCE = '{repository}/baseline/baseline2_evidence.txt'

path = VIDEOS.format(repository=REPOSITORY)
names = ['corpus_id', 'video_id']
videos = pd.read_table(path, delim_whitespace=True, header=None, names=names)

argmax_tagger = ArgMaxTagger()

TEMPLATE_SUBMISSION = \
    '{corpus_id} {video_id} {shot_id} {person_name} {confidence:.3f}\n'
TEMPLATE_EVIDENCE = \
    '{person_name} {corpus_id} {video_id} {modality} {timestamp:.3f}\n'

ALLOWED = set('abcdefghijklmnopqrstuvwxyz_')
def get_valid_person_name(person_name):
    used = set(person_name)
    remove = used - ALLOWED
    for letter in remove:
        person_name = person_name.replace(letter, '')
    return person_name

path_submission = SUBMISSION.format(repository=REPOSITORY)
with open(path_submission, 'w') as fp_submission:

    mapping = {}
    evidences = {}

    for _, (corpus_id, video_id)    in videos.iterrows():

        uri = corpus_id + '/' + video_id

        # load shots as pyannote.Annotation
        path = SHOTS.format(repository=REPOSITORY, uri=uri)
        names = ['corpus_id', 'video_id', 'shot_id', 'start', 'end']
        dtype = {'shot_id': str}
        shots = pd.read_table(path, delim_whitespace=True, header=None, names=names, dtype=dtype)
        pyannote_shots = Annotation(uri=uri)
        for _, (_, _, shot_id, start, end) in shots.iterrows():
            pyannote_shots[Segment(start, end), shot_id] = shot_id

        # load face clustering as dictionary mapping {track_id: cluster_id}
        path = FACE_CLUSTERING.format(repository=REPOSITORY, uri=uri)
        names = ['track_id', 'cluster_id']
        face_clustering = pd.read_table(path, delim_whitespace=True, header=None, names=names)
        mapping = {track_id: cluster_id
                   for _, (track_id, cluster_id) in face_clustering.iterrows()}

        # load face tracking as pyannote.Annotation
        path = FACE_TRACKING.format(repository=REPOSITORY, uri=uri)
        names = ['time', 'track_id', 'left', 'top', 'right', 'bottom']
        face_tracking = pd.read_table(path, delim_whitespace=True, header=None, names=names)
        pyannote_face = Annotation(uri=uri)
        for track_id, track in face_tracking.groupby('track_id'):
            start = track['time'].min()
            end = track['time'].max()
            label = mapping.get(track_id, None)
            if label is None:
                SKIP = 'Skipping track #{track_id} ({duration:d} ms) in {video_id}'
                print(SKIP.format(track_id=track_id, duration=int(1000*(end-start)), video_id=video_id))
            pyannote_face[Segment(start, end), track_id] = label

        # load names as pyannote.Annotation
        path = OCR.format(repository=REPOSITORY, uri=uri)
        names = ['start', 'end', 'start_frame', 'end_frame', 'name', 'confidence']
        pyannote_ocr = Annotation(uri=uri)
        try:
            ocr = pd.read_table(path, delim_whitespace=True, header=None, names=names)
            for _, (start, end, _, _, name, _) in ocr.iterrows():
                pyannote_ocr[Segment(start, end)] = name
        except pandas.parser.CParserError as e:
            pass

        # name each person by most co-occurring OCR name
        if not pyannote_ocr:
            named_face = Annotation(uri=uri)
        else:
            named_face = argmax_tagger(pyannote_ocr, pyannote_face)
            named_face = named_face.subset(pyannote_ocr.labels())

        path = FUSION.format(repository=REPOSITORY, uri=uri)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as fp:

            duplicates = dict()

            for (segment, track_id), (_, shot_id) in named_face.co_iter(pyannote_shots):

                original_person_name = named_face[segment, track_id]

                person_name = mapping.setdefault(
                    original_person_name, get_valid_person_name(original_person_name))

                if person_name not in evidences:
                    segment, _ = list(itertools.islice(pyannote_ocr.subset([original_person_name]).itertracks(), 1))[0]
                    evidences[person_name] = {
                        'person_name': person_name,
                        'corpus_id': corpus_id,
                        'video_id': video_id,
                        'modality': 'written',
                        'timestamp': segment.middle
                    }

                if person_name in duplicates.setdefault(shot_id, set([])):
                    continue
                duplicates[shot_id].add(person_name)

                line = TEMPLATE_SUBMISSION.format(
                    corpus_id=corpus_id, video_id=video_id, shot_id=shot_id,
                    person_name=person_name, confidence=1.0)
                fp.write(line)
                fp_submission.write(line)

path_evidence = EVIDENCE.format(repository=REPOSITORY)
with open(path_evidence, 'w') as fp_evidence:
    for person_name, evidence in evidences.items():
        line = TEMPLATE_EVIDENCE.format(**evidence)
        fp_evidence.write(line)
