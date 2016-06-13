# Propagate OCR on speaker diarization

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
SPEAKERS = '{repository}/speaker_diarization/{uri}.sd'
FUSION = '{repository}/baseline/baseline1/{uri}.txt'
SUBMISSION = '{repository}/baseline/baseline1_submission.txt'
EVIDENCE = '{repository}/baseline/baseline1_evidence.txt'

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

    for _, (corpus_id, video_id) in videos.iterrows():

        uri = corpus_id + '/' + video_id

        # load shots as pyannote.Annotation
        path = SHOTS.format(repository=REPOSITORY, uri=uri)
        names = ['corpus_id', 'video_id', 'shot_id', 'start', 'end']
        dtype = {'shot_id': str}
        shots = pd.read_table(path, delim_whitespace=True, header=None, names=names, dtype=dtype)
        pyannote_shots = Annotation(uri=uri)
        for _, (_, _, shot_id, start, end) in shots.iterrows():
            pyannote_shots[Segment(start, end), shot_id] = shot_id

        # load speaker diarization as pyannote.Annotation
        path = SPEAKERS.format(repository=REPOSITORY, uri=uri)
        names = ['corpus_id', 'video_id', 'start', 'end', 'label', 'gender']
        speakers = pd.read_table(path, delim_whitespace=True, header=None, names=names)
        pyannote_speakers = Annotation(uri=uri)
        for _, (_, _, start, end, label, _) in speakers.iterrows():
            pyannote_speakers[Segment(start, end)] = label
        pyannote_speakers = pyannote_speakers.anonymize_labels(generator='int')

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

        # name each speaker by most co-occurring OCR name
        if not pyannote_ocr:
            named_speakers = Annotation(uri=uri)
        else:
            named_speakers = argmax_tagger(pyannote_ocr, pyannote_speakers)
            named_speakers = named_speakers.subset(pyannote_ocr.labels())

        path = FUSION.format(repository=REPOSITORY, uri=uri)
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        with open(path, 'w') as fp:

            duplicates = dict()

            for (speech_turn, track), (_, shot_id) in named_speakers.co_iter(pyannote_shots):

                original_person_name = named_speakers[speech_turn, track]

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
