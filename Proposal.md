# Project Proposal

**Project Title:** Automated AI-Based Visual Inspection System for Car Exterior Defect Detection

| **Item** | **Details** |
|----------|-------------|
| **Intern Name** | LOU Chumdararith |
| **Company Supervisor** | Mr. CHAN Ritheareach |
| **Academic Advisor** | Dr. VALY Dona |
| **Organization/University** | AI Farm Robotics / Institute of Technology of Cambodia |
| **Duration** | 12 Weeks / 3 Months |
| **Date** | 03/July/2026 |

---

# 1. Executive Summary

Quality control in automotive manufacturing is critical but traditionally relies on manual visual inspection, which is time-consuming, subjective, and prone to human fatigue. This project proposes the development of an Artificial Intelligence (AI) computer vision model capable of automatically detecting and classifying common exterior defects on vehicles. By leveraging deep learning, this system aims to assist quality assurance teams in identifying surface anomalies, missing components, and structural deformities with high accuracy and speed.

---

# 2. Problem Statement

In the current vehicle inspection process, inspectors must check for dozens of defect types. While internal assembly defects (like wiring routing) require human expertise, exterior appearance defects (scratches, dents, stains, missing parts) are highly repetitive. Relying solely on human vision for these exterior checks leads to inconsistent quality control and bottlenecks in the production line. There is a need for an automated, objective, and scalable vision system to handle these specific exterior inspections.

---

# 3. Project Objectives

The primary objective is to design, train, and evaluate a deep learning model for car exterior defect detection.

### Specific Goals

- **Dataset Creation:** Compile and annotate a dataset of car exterior images featuring targeted defects.
- **Model Development:** Train an object detection model to identify and localize specific defect classes.
- **Performance Optimization:** Achieve a target mean Average Precision (mAP) of >80% on the validation set.
- **Prototype Demonstration:** Deploy the trained model in a simple inference pipeline to demonstrate real-time or batch defect detection.

---

# 4. Scope of Work

To ensure the project is achievable within the internship timeframe, the scope is strictly limited to exterior, visually detectable defects.

## In-Scope Defect Classes

### Surface Anomalies
- Scratch/Chip
- Stain
- Dirty
- Bird Droppings Stain

### Geometric Deformities
- Dent
- Ding
- Deform

### Assembly/Part Issues
- Missing Part
- Bolt/Screw Missing (on exterior trim/wheels)
- Colour Unmatch

## Out-of-Scope

- Internal mechanical defects (Wiring, Fluid Leaks, Hose Routing).
- Tactile defects (Loose parts, Clip unlocks, Tightness).
- Complex 3D gap/flushness measurements (Poor Fit) requiring specialized laser hardware.

---

# 5. Methodology & Technical Approach

The project will follow a standard Machine Learning lifecycle.

## Phase 1: Data Collection & Preprocessing

- Gather images from open-source automotive datasets, web scraping, or company-provided data.
- Apply data augmentation (rotation, scaling, brightness adjustments) to increase dataset diversity and prevent overfitting.

## Phase 2: Data Annotation

- Use annotation tools (like Roboflow, CVAT, or LabelImg) to draw bounding boxes around defects and assign class labels.

## Phase 3: Model Selection & Training

- Utilize an object detection architecture, such as YOLOv8 or YOLOv26, due to its high speed and accuracy trade-off.
- Apply Transfer Learning using a model pre-trained on the COCO dataset to speed up convergence.

## Phase 4: Evaluation & Testing

- Evaluate the model using standard metrics:
  - Precision
  - Recall
  - F1-Score
  - mAP@0.5
- Conduct inference on a held-out "test set" to simulate real-world performance.

---

# 6. Project Timeline (12-Week Schedule)

| **Week** | **Phase** | **Key Activities & Milestones** |
|----------|-----------|----------------------------------|
| **1–2** | Research & Setup | Literature review on CV in manufacturing. Setup development environment (Python, PyTorch/Ultralytics). Finalize defect classes. |
| **3–5** | Data Pipeline | Aim for 500–1000 images per class. |
| **6–7** | Model Training | Configure YOLO model. Run initial training epochs. Analyze loss curves and adjust hyperparameters (learning rate, batch size). |
| **8–9** | Optimization | Address class imbalances. Fine-tune the model. Implement data augmentation strategies to improve Recall on hard-to-detect classes (like small scratches). |
| **10–11** | Testing & UI | Evaluate final model metrics. Build a simple inference script or Streamlit web app to allow users to upload a car image and see detected defects. |
| **12** | Documentation | Write a final internship report. Prepare presentation slides. Handover code and model weights to the supervisor. |

---

# 7. Expected Deliverables

- **Annotated Dataset:** A clean, labeled dataset of car exterior defects ready for future training.
- **Trained AI Model:** The final model weights (`.pt` file) and configuration files.
- **Source Code:** Well-documented Python code for training, evaluation, and inference.
- **Final Report:** A comprehensive document detailing the methodology, challenges faced, results, and recommendations for future work.
- **Final Presentation:** A slide deck summarizing the project for stakeholders.

---

# 8. Resources Required

## Hardware

- Access to a NVIDIA GPU for model training.

## Software

- Python 3.10 or higher
- Ultralytics YOLO framework
- OpenCV
- Roboflow/CVAT for annotation

## Data

- Access to historical inspection images from the company (if available) or permission to scrape public datasets.
