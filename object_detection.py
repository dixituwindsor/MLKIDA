import math
from dataclasses import dataclass
import numpy as np
from typing import List
from supervision.geometry.dataclasses import Point
from supervision.video.dataclasses import VideoInfo
from supervision.video.sink import VideoSink
from ultralytics import YOLO
from ByteTrack.yolox.tracker.byte_tracker import BYTETracker, STrack
from supervision.tools.line_counter import LineCounter, LineCounterAnnotator
from supervision.video.source import get_video_frames_generator
from supervision.notebook.utils import show_frame_in_notebook
from supervision.tools.detections import Detections, BoxAnnotator
from supervision.draw.color import ColorPalette
from onemetric.cv.utils.iou import box_iou_batch
from tqdm import tqdm


# converts Detections into format that can be consumed by match_detections_with_tracks function
def detections2boxes(detections: Detections) -> np.ndarray:
    return np.hstack((
        detections.xyxy,
        detections.confidence[:, np.newaxis]
    ))


# converts List[STrack] into format that can be consumed by match_detections_with_tracks function
def tracks2boxes(tracks: List[STrack]) -> np.ndarray:
    return np.array([
        track.tlbr
        for track
        in tracks
    ], dtype=float)


# matches our bounding boxes with predictions
def match_detections_with_tracks(detections: Detections,tracks: List[STrack]) -> Detections:
    if not np.any(detections.xyxy) or len(tracks) == 0:
        return np.empty((0,))

    tracks_boxes = tracks2boxes(tracks=tracks)
    iou = box_iou_batch(tracks_boxes, detections.xyxy)
    track2detection = np.argmax(iou, axis=1)

    tracker_ids = [None] * len(detections)

    for tracker_index, detection_index in enumerate(track2detection):
        if iou[tracker_index, detection_index] != 0:
            tracker_ids[detection_index] = tracks[tracker_index].track_id

    return tracker_ids


@dataclass(frozen=True)
class BYTETrackerArgs:
    track_thresh: float = 0.25
    track_buffer: int = 30
    match_thresh: float = 0.8
    aspect_ratio_thresh: float = 3.0
    min_box_area: float = 1.0
    mot20: bool = False


def count_objects_in_video(video_file_path: str, output_video_path: str) -> dict:
    # Initialize YOLO model
    model = YOLO('yolo_model/best.pt')
    model.fuse()

    CLASS_NAMES_DICT = model.model.names
    print(CLASS_NAMES_DICT)
    CLASS_ID = [0, 1]

    # Initialize line counter
    LINE_START = Point(0, 0)
    LINE_END = Point(0, 0)
    # create BYTETracker instance
    byte_tracker = BYTETracker(BYTETrackerArgs())
    # create VideoInfo instance
    video_info = VideoInfo.from_video_path(video_file_path)
    # create frame generator
    generator = get_video_frames_generator(video_file_path)
    # create LineCounter instance
    line_counter = LineCounter(start=LINE_START, end=LINE_END)
    # create instance of BoxAnnotator and LineCounterAnnotator
    box_annotator = BoxAnnotator(color=ColorPalette(), thickness=4, text_thickness=4, text_scale=2)
    line_annotator = LineCounterAnnotator(thickness=4, text_thickness=4, text_scale=2)

    # Initialize a list to collect all detections
    all_detections = []

    # open target video file
    with VideoSink(output_video_path, video_info) as sink:
        # loop over video frames
        for frame in tqdm(generator, total=video_info.total_frames):
            # model prediction on single frame and conversion to supervision Detections
            results = model(frame)
            detections = Detections(
                xyxy=results[0].boxes.xyxy.cpu().numpy(),
                confidence=results[0].boxes.conf.cpu().numpy(),
                class_id=results[0].boxes.cls.cpu().numpy().astype(int)
            )
            # filtering out detections with unwanted classes
            mask = np.array([class_id in CLASS_ID for class_id in detections.class_id], dtype=bool)
            detections.filter(mask=mask, inplace=True)
            # tracking detections
            tracks = byte_tracker.update(
                output_results=detections2boxes(detections=detections),
                img_info=frame.shape,
                img_size=frame.shape
            )
            tracker_id = match_detections_with_tracks(detections=detections, tracks=tracks)
            detections.tracker_id = np.array(tracker_id)
            # filtering out detections without trackers
            mask = np.array([tracker_id is not None for tracker_id in detections.tracker_id], dtype=bool)
            detections.filter(mask=mask, inplace=True)
            # format custom labels
            labels = [
                f"#{tracker_id} {CLASS_NAMES_DICT[class_id]} {confidence:0.2f}"
                for _, confidence, class_id, tracker_id
                in detections
            ]
            # updating line counter
            line_counter.update(detections=detections)
            # annotate and display frame
            frame = box_annotator.annotate(frame=frame, detections=detections, labels=labels)
            line_annotator.annotate(frame=frame, line_counter=line_counter)
            sink.write_frame(frame)

            # Append detections to the list for counting
            all_detections.extend(detections)

    print(all_detections)
    FEEDER_MITES_ID = 0
    PREDATORY_MITES_ID = 1
    tracker = 1

    # Initialize sets to collect unique IDs for each class
    unique_ids_feeder_mites = set()
    unique_ids_predatory_mites = set()

    # Iterate over all detections to collect unique IDs for each class
    for detection in all_detections:
        # Assuming the class ID is the third element in the tuple
        class_id = detection[2]
        if class_id == FEEDER_MITES_ID:
            unique_ids_feeder_mites.add(detection[3])  # Assuming the tracker ID is the fourth element
        elif class_id == PREDATORY_MITES_ID:
            unique_ids_predatory_mites.add(detection[3])  # Assuming the tracker ID is the fourth element

    # Count the unique IDs for each class
    count_feeder_mites = len(unique_ids_feeder_mites)
    count_predatory_mites = math.ceil(len(unique_ids_predatory_mites) / tracker)

    # Print the counts
    print(f"Feeder-mites: {count_feeder_mites} unique IDs")
    print(f"Predatory-mites: {count_predatory_mites} unique IDs")

    return {'feeder-mites': count_feeder_mites, 'predatory-mites': count_predatory_mites}


if __name__ == "__main__":
    print(count_objects_in_video(video_file_path="4.mp4", output_video_path="output_video.mp4"))