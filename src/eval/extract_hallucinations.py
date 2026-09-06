import os
import cv2
import glob
import numpy as np
from ultralytics import YOLO

# --- Configuration ---
BASE_DIR = "/Users/macbook/Documents/ITC8/Internship/AI Farm/Testing/car_defect_detection"

# Adjust this path if your clean images are stored in a different folder
CLEAN_IMG_DIR = os.path.join(BASE_DIR, "data/processed/clean_cars/images/clean_eval") 
OUTPUT_DIR = os.path.join(BASE_DIR, "hallucination_samples")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Model paths
MODELS = {
    "surgical_early": os.path.join(BASE_DIR, "runs/segment/seesaw_surgical_early/weights/best.pt"),
    "baseline_m5": os.path.join(BASE_DIR, "runs/segment/stage1_head_warmup_7cls_extended/stage1_head_warmup_7cls_extended/weights/best.pt"),
    "model_4": os.path.join(BASE_DIR, "runs/segment/model5_resume_adapt_7cls/stage2_differential_finetune_7cls/weights/best.pt"),
    "objectness_branch": os.path.join(BASE_DIR, "runs/segment/seesaw_sugical_objectness/weights/seesaw_sugical_objectness.pt"),
}

# Target hallucinations to extract based on your benchmark results
# Format: "model_key": "class_name"
TARGET_HALLUCINATIONS = {
    "baseline_m5": "broken_lamp",
    "surgical_early": "broken_lamp",
    "objectness_branch": "disjoint_part"
}

# How many sample images to extract per model/class
MAX_SAMPLES_PER_TARGET = 2

# Confidence threshold to consider it a hallucination
CONF_THRESHOLD = 0.25 

def get_image_paths(directory):
    """Gather all image paths from a directory."""
    if not os.path.exists(directory):
        return []
    exts = ["*.jpg", "*.jpeg", "*.png", "*.bmp", "*.JPG", "*.PNG"]
    paths = []
    for ext in exts:
        paths.extend(glob.glob(os.path.join(directory, ext)))
    return sorted(paths)

def draw_predictions(img, results, class_name_to_find):
    """Draw masks and boxes for a specific class on the image."""
    plotted_img = img.copy()
    found = False
    
    if results[0].masks is not None and results[0].boxes is not None:
        masks = results[0].masks.data.cpu().numpy()
        boxes = results[0].boxes.xyxy.cpu().numpy()
        classes = results[0].boxes.cls.cpu().numpy().astype(int)
        confs = results[0].boxes.conf.cpu().numpy()
        names = results[0].names
        
        for mask, box, cls_id, conf in zip(masks, boxes, classes, confs):
            if conf < CONF_THRESHOLD:
                continue
                
            cls_name = names[cls_id]
            if cls_name == class_name_to_find:
                found = True
                # Draw mask (Red for broken_lamp, Magenta for disjoint_part)
                color = (0, 0, 255) if cls_name == "broken_lamp" else (255, 0, 255) 
                mask_bool = mask.astype(bool)
                
                # Ensure mask matches image dimensions (in case of internal resizing)
                if mask_bool.shape[:2] != plotted_img.shape[:2]:
                    mask_bool = cv2.resize(mask_bool.astype(np.uint8), (plotted_img.shape[1], plotted_img.shape[0])).astype(bool)
                
                plotted_img[mask_bool] = plotted_img[mask_bool] * 0.5 + np.array(color) * 0.5
                
                # Draw box and text
                x1, y1, x2, y2 = map(int, box)
                cv2.rectangle(plotted_img, (x1, y1), (x2, y2), color, 2)
                label = f"{cls_name} {conf:.2f}"
                cv2.putText(plotted_img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                
    return plotted_img, found

def main():
    print("Loading models...")
    loaded_models = {}
    for name, path in MODELS.items():
        if os.path.exists(path):
            print(f"Loading {name} from {path}")
            loaded_models[name] = YOLO(path)
        else:
            print(f"WARNING: Model path not found for {name}: {path}")
            
    print(f"\nScanning clean images in: {CLEAN_IMG_DIR}")
    if not os.path.exists(CLEAN_IMG_DIR):
        print(f"ERROR: Clean image directory not found at {CLEAN_IMG_DIR}")
        print("Please update the CLEAN_IMG_DIR variable in the script if your clean images are elsewhere.")
        return
        
    image_paths = get_image_paths(CLEAN_IMG_DIR)
    print(f"Found {len(image_paths)} clean images.")
    
    if not image_paths:
        print("No images found to process.")
        return

    # Trackers for how many samples we've collected
    collected_counts = {model_name: 0 for model_name in TARGET_HALLUCINATIONS}
    
    print("\nStarting inference and extraction...")
    for img_path in image_paths:
        # Stop if we have collected enough for all targets
        if all(count >= MAX_SAMPLES_PER_TARGET for count in collected_counts.values()):
            print("Collected maximum samples for all targets. Stopping early.")
            break
            
        img = cv2.imread(img_path)
        if img is None:
            continue
            
        img_name = os.path.basename(img_path)
        
        # Run inference for each target model
        for model_name, target_class in TARGET_HALLUCINATIONS.items():
            if collected_counts[model_name] >= MAX_SAMPLES_PER_TARGET:
                continue
                
            if model_name not in loaded_models:
                continue
                
            model = loaded_models[model_name]
            
            # Run standard inference. 
            # Note: Standard inference is usually sufficient to catch false positives (hallucinations).
            results = model(img, verbose=False, conf=CONF_THRESHOLD)
            
            plotted_img, found = draw_predictions(img, results, target_class)
            
            if found:
                collected_counts[model_name] += 1
                out_filename = f"{model_name}_{target_class}_{collected_counts[model_name]}_{img_name}"
                out_path = os.path.join(OUTPUT_DIR, out_filename)
                cv2.imwrite(out_path, plotted_img)
                print(f"✅ Saved: {out_filename}")

    print("\n--- Extraction Complete ---")
    for model_name, count in collected_counts.items():
        print(f"{model_name} ({TARGET_HALLUCINATIONS[model_name]}): {count} images saved.")
    print(f"Results saved to: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()