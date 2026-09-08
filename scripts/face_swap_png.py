#!/usr/bin/env python3
"""Face swap - write frames to PNG then combine with ffmpeg"""
import insightface
import cv2
from pathlib import Path
import os
import subprocess
import shutil

def main():
    # Initialize
    print("Loading models...")
    app = insightface.app.FaceAnalysis(name='buffalo_l', root=str(Path.home() / '.insightface'))
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    from insightface.model_zoo.inswapper import INSwapper
    model_path = str(Path.home() / '.insightface/models/inswapper_128.onnx')
    swapper = INSwapper(model_file=model_path)
    
    # Load source face
    source_img = cv2.imread("/home/sword/Downloads/Untitled.jpg")
    source_faces = app.get(source_img)
    if not source_faces:
        print("No face found in source image")
        return
    source_face = source_faces[0]
    print("Models loaded, processing...")
    
    # Process video
    cap = cv2.VideoCapture("chris_holt_tiny.mp4")
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"Video: {width}x{height}, {fps:.1f}fps, {total_frames} frames")
    
    # Create temp directory for frames
    tmpdir = "/tmp/face_swapped_frames"
    os.makedirs(tmpdir, exist_ok=True)
    # Clear old frames
    for f in os.listdir(tmpdir):
        os.remove(os.path.join(tmpdir, f))
    
    # Process frames
    frame_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        if frame_count % 30 == 0:
            print(f"Frame {frame_count}/{total_frames}")
        
        # Get faces and swap
        frame_faces = app.get(frame)
        if frame_faces:
            target_face = frame_faces[0]
            swapped = swapper.get(frame, target_face, source_face, paste_back=True)
        else:
            swapped = frame
        
        # Save as PNG
        cv2.imwrite(os.path.join(tmpdir, f"frame_{frame_count:04d}.png"), swapped)
    
    cap.release()
    print(f"Processed {frame_count} frames")
    
    # Combine frames into video
    print("Combining frames into video...")
    concat_cmd = [
        'ffmpeg', '-y',
        '-framerate', str(fps),
        '-i', os.path.join(tmpdir, 'frame_%04d.png'),
        '-c:v', 'libx264',
        '-preset', 'fast',
        '-crf', '23',
        '-pix_fmt', 'yuv420p',
        'face_swapped.mp4'
    ]
    subprocess.run(concat_cmd, check=True, capture_output=True)
    
    # Clean up
    shutil.rmtree(tmpdir, ignore_errors=True)
    print("Face swap complete: face_swapped.mp4")

if __name__ == "__main__":
    main()
