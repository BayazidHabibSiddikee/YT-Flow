#!/usr/bin/env python3
"""Face swap - process frames in smaller chunks to save memory"""
import insightface
import cv2
import numpy as np
from pathlib import Path
import os
import tempfile
import shutil

def get_face_swapper():
    """Initialize face analysis and swapper"""
    app = insightface.app.FaceAnalysis(name='buffalo_l', root=str(Path.home() / '.insightface'))
    app.prepare(ctx_id=0, det_size=(640, 640))
    
    model_path = str(Path.home() / '.insightface/models/inswapper_128.onnx')
    from insightface.model_zoo.inswapper import INSwapper
    swapper = INSwapper(model_file=model_path)
    
    return app, swapper

def swap_face_chunked(video_path, source_image_path, output_path, frames_per_chunk=20):
    """Perform face swap on video, processing in chunks"""
    app, swapper = get_face_swapper()
    
    # Get source face
    source_img = cv2.imread(source_image_path)
    if source_img is None:
        raise ValueError(f"Could not read source image: {source_image_path}")
    source_faces = app.get(source_img)
    if not source_faces:
        raise ValueError("No face found in source image")
    source_face = source_faces[0]
    print(f"Source face loaded")
    
    # Process video
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f'Video: {width}x{height}, {fps:.1f}fps, {total_frames} frames')
    
    # Create temp directory for chunks
    tmpdir = tempfile.mkdtemp()
    try:
        chunk_frames = []
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        chunk_num = 0
        
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            
            if i % 30 == 0:
                print(f"Frame {i}/{total_frames}")
            
            # Get faces and swap
            frame_faces = app.get(frame)
            if frame_faces:
                target_face = frame_faces[0]
                swapped = swapper.get(frame, target_face, source_face, paste_back=True)
            else:
                swapped = frame
            
            chunk_frames.append(swapped)
            
            # Process chunk
            if len(chunk_frames) >= frames_per_chunk:
                # Write chunk to temp file
                chunk_path = os.path.join(tmpdir, f"chunk_{chunk_num:04d}.mp4")
                out = cv2.VideoWriter(chunk_path, fourcc, fps, (width, height))
                for f in chunk_frames:
                    out.write(f)
                out.release()
                chunk_frames = []
                chunk_num += 1
                # Force garbage collection
                import gc
                gc.collect()
        
        # Process remaining frames
        if chunk_frames:
            chunk_path = os.path.join(tmpdir, f"chunk_{chunk_num:04d}.mp4")
            out = cv2.VideoWriter(chunk_path, fourcc, fps, (width, height))
            for f in chunk_frames:
                out.write(f)
            out.release()
        
        cap.release()
        
        # Concatenate all chunks using ffmpeg
        concat_file = os.path.join(tmpdir, "concat.txt")
        with open(concat_file, 'w') as f:
            for i in range(chunk_num + 1):
                f.write(f"file 'chunk_{i:04d}.mp4'\n")
        
        concat_cmd = [
            'ffmpeg', '-y',
            '-f', 'concat', '-safe', '0',
            '-i', concat_file,
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '23',
            '-c:a', 'aac',
            output_path
        ]
        
        import subprocess
        subprocess.run(concat_cmd, check=True, capture_output=True)
        print(f"Face swap complete: {output_path}")
        
    finally:
        # Clean up temp directory
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    return output_path

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("video", help="Input video path")
    parser.add_argument("source_face", help="Source face image path")
    parser.add_argument("output", help="Output video path")
    args = parser.parse_args()
    
    swap_face_chunked(args.video, args.source_face, args.output)
