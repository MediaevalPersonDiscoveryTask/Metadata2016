# PersonDiscovery2016Metadata

##### `/lists`

  This directory contains list of videos to be processed:

  * `3-24.txt` contains the list of videos in corpus `3-24`.  
  * `DW.txt` contains the list of videos in corpus `DW`.
  * `INA.txt` contains the full list of videos in corpus `INA`
  * `INA.test.txt` contains the subset of `INA` corpus that needs to be processed.

  Each file contains one line per video, using the following convention:  
  `{video_id}`  
  * `video_id` is the video identifier within the corpus

##### `/shots` (segmentation into shots)

  This directory contains one `{corpus_id}/{video_id}.shot` file per video.  
  Each file contains one line per shot, using the following convention:  
  `corpus_id video_id shot_id shot_start shot_end`  
  * `corpus_id` is the corpus identifier (`DW`, `INA` or `3-24`)
  * `video_id` is the video identifier within the corpus
  * `shot_id` is the shot identifier within the video
  * `shot_start` is the shot start time in seconds
  * `shot_end` is the shot end time in seconds

  Each shot is therefore uniquely identified by its tuple `(corpus_id, video_id, shot_id)`.

##### `/face_tracking` (face tracking)

  This directory contains one `{corpus_id}/{video_id}.txt` file per video.
  Each file contains one line per face per timestamp, using the following convention:
  `timestamp track_id left top right bottom`
  * `timestamp` is the elapsed time since the beginning of the video
  * `track_id` is the identifier of the face track with the video
  * `left` is the position of the face bounding box left boundary, normalized by the video width
  * `right` is the position of the face bounding box right boundary, normalized by the video width
  * `top` is the position of the face bounding box top boundary, normalized by the video height
  * `bottom` is the position of the face bounding box bottom boundary, normalized by the video height

  Each face track is therefore uniquely identified by the tuple `(corpus_id, video_id, track_id)`

##### `/face_clustering` (face clustering)

  This directory contains one `{corpus_id}/{video_id}.txt` file per video.
  Each file contains one line per face track, using the following convention:
  `track_id cluster_id`  
  * `track_id` as defined in face tracking files
  * `cluster_id` is the identifier of the face track cluster

  Note that face clustering is applied within each video, not accross all videos.
  Each face track cluster is therefore uniquely identified by the tuple `(corpus_id, video_id, cluster_id)`.

##### `/optical_character_recognition` (OCR + name detection)

  This directory contains one `{corpus_id}/{video_id}.txt` file per video.
  Each file contains one line per detected overlaid names, using the following convention:
  `start_time end_time start_frame end_frame person_name confidence`  
  * `start_time` is the elapsed time since the beginning of the video when overlaid name appears
  * `end_time` is the elapsed time since the beginning of the video when overlaid name disappears
  * `start_frame` is the video frame index when overlaid name appears
  * `end_frame` is the video frame index when overlaid name disappears
  * `person_name` is the normalized person name
  * `confidence` is a detection confidence score between 0 and 1

  Note that empty files indicate that no names were detected.


##### `/speech_transcription` (automatic speech recognition)

This directory contains one `{corpus_id}/{video_id}.txt` file per video.  
Each file contains one line per word, using the following convention:  
`corpus_id video_id start_time end_time word confidence`  
* `corpus_id` is the corpus identifier (`DW`, `INA` or `3-24`)
* `video_id` is the video identifier within the corpus
* `start_time` is the elapsed time since the beginning of the video when word starts
* `end_time` is the elapsed time since the beginning of the video when word ends
* `word` is the actual recognized word
* `confidence` is a recognition confidence score between 0 and 1
