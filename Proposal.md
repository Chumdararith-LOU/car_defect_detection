# **PROJECT PROPOSAL (REVISED)**

**Project Title:** Automated Multi-Stage AI Pipeline for Component-Aware Automotive Exterior Defect Detection and Industrial Quality Inspection

**Intern Name:** LOU Chumdararith

**Company Supervisor:** Mr. CHAN Ritheareach

**Academic Advisor:** Dr. VALY Dona

**Organization/University:** AI Farm Robotics / Institute of Technology of Cambodia

**Duration:** 12 Weeks / 3 Months

**Date:** July 08, 2026

**Document Version:** 2.0 (Industrial Research & Production Revision)

## **1\. Executive Summary**

Quality control in automotive manufacturing is critical but traditionally relies on manual visual inspection, which is time-consuming, highly subjective, and prone to human fatigue. While simple AI classification projects are common in academic environments, real-world factory integration requires a production-grade inspection system capable of high-throughput pre-screening, ultra-precise localized anomaly detection, and granular contextual reporting.

This updated project proposes a **Multi-Stage Intelligent Visual Inspection Pipeline** that leverages four distinct datasets representing different computer vision paradigms. Rather than deploying a single, isolated neural network, this system coordinates a series of specialized models:

1. A binary salient object detection (SOD) model acting as a high-speed pre-screening filter.
2. A multi-class instance segmentation core engine utilizing tiling-based inference to detect micro-level paint scratches, cracks, and dents.
3. A component segmentation model to map structural panels (e.g., doors, hood, fenders).

By calculating the geometric intersections between these layers, the final system dynamically isolates defects, generates automatic crops of damaged areas, and reports precise panel-specific diagnostics on an interactive industrial dashboard.

## **2\. Problem Statement**

Automotive final-assembly lines operate at high speeds, making automated inspection pipelines sensitive to computational bottlenecks and scale variations. Two primary challenges limit the effectiveness of standard single-model inspection systems on real-world factory floors:

1. **The Tiny Defect Problem (Scale Variance):** In high-resolution images capturing an entire vehicle or complete panels, critical defects such as thin scratches, minor paint chips, or glass hairline cracks occupy an extremely small fraction of the image canvas (often $\< 0.1\\%$ of total pixels). Standard object detectors downsample input frames, which completely erases these tiny features from deeper feature maps.
2. **Lack of Contextual Awareness:** Industrial inspectors need to know more than just *what* the defect is; they need to know *where* it is located relative to the vehicle's bill of materials (e.g., *"Scratch on Front-Door"* vs. *"Scratch on Rear-Bumper"*). A raw bounding box classifier lacks the spatial awareness to correlate surface anomalies with specific body panels.

To transition visual inspection from a basic research study to a viable factory solution, there is a clear industrial need for a multi-stage software pipeline that addresses scale issues using high-resolution tiling and generates contextual, panel-specific anomaly reports.

## **3\. Project Objectives**

The primary objective of this project is to research, build, and deploy a multi-stage deep learning pipeline for car exterior defect detection capable of processing high-resolution industrial image and video feeds. Specific goals include:

* **Objective 1: Multi-Model Pipeline Engineering:** Design and train a hierarchical inference pipeline containing:
  * A lightweight binary pre-screener model ($M\_{\\text{binary}}$) trained on salient object boundaries to quickly filter out clean parts.
  * A high-precision multi-class instance segmentation core model ($M\_{\\text{core}}$) trained on unified COCO and custom defect annotations.
  * A structural panel segmenter model ($M\_{\\text{panel}}$) trained on body panel datasets to localize physical boundaries.
* **Objective 2: Slicing Aided Hyper-Inference (SAHI) Integration:** Implement a tiling and sliding-window inference pipeline to solve the "Tiny Defect Problem," allowing the models to process sub-grid patches of high-resolution image inputs without losing fine spatial detail.
* **Objective 3: Spatial Context Mapping:** Programmatically compute the geometric intersection over union ($\\text{IoU}$) and contour containment between localized defect polygons and structural panel segmentation masks to automatically identify the exact body panel affected.
* **Objective 4: Production Dashboard UI:** Build a fully functional, high-throughput inspection dashboard (Streamlit or Gradio) that:
  * Handles image and video uploads.
  * Allows operators to query defects by specific panels (e.g., *"Show defects on Hood only"*).
  * Generates pixel-level severity scores and outputs automated cropped close-ups of each detected defect with highlighted boundaries.
* **Objective 5: Edge Optimization Research (Optional Milestone):** Benchmark lightweight model backbones (such as YOLOv8-Nano) to evaluate deployment feasibility on handheld smartphone inspection devices for floor workers.

## **4\. Scope of Work**

The project scope is strictly limited to exterior, visually detectable defects and vehicle components, utilizing the combined taxonomy of four available datasets.

                                 \[SYSTEM PIPELINE SCOPE\]
                                             │
         ┌───────────────────────────────────┼───────────────────────────────────┐
         ▼                                   ▼                                   ▼
   \[IN-SCOPE DEFECTS\]              \[IN-SCOPE VEHICLE PARTS\]               \[OUT-OF-SCOPE\]
   \- Scratch / Paint Chip          \- Hood / Trunk / Roof                \- Internal Wiring
   \- Dent / Ding / Deform          \- Front / Back Bumper                \- Hose / Fluid leaks
   \- Crack / Glass Shatter         \- Front / Back Doors                 \- Tightness / Torque
   \- Broken Lamp / Taillight       \- Quarter-Panel / Fender             \- Underbody Mechanics
   \- Corrosion / Rust / Flaking    \- Windshield / Windows / Mirrors     \- 3D Gap & Flushness
   \- Missing Part                  \- Wheels / Tires                     \- Tactile / Loose Clips

## **5\. Methodology & Technical Approach**

The system architecture is organized as an integrated, multi-stage software pipeline:

\[Incoming Frame\] ──► Stage 1 (Binary SOD) ──► Anomaly? ──► \[Yes\] ──► Stage 2 (Tiled Segmentation) ──► Crop & Analyze
                        │                                               │
                        ▼ \[No\]                                          ▼ (Intersect with Stage 3 Panel Mask)
                    \[Pass Car\]                                    \[Factory Dashboard Diagnostic Output\]

### **Stage 1: Salient Pre-Screening**

The system processes the incoming image using a lightweight model trained on **Dataset D (CarDD\_SOD)**. If no anomalous salient areas are flagged above a confidence threshold $\\tau\_{\\text{binary}}$, the frame bypassed. This minimizes processing delays for defect-free vehicles on the conveyor belt.

### **Stage 2: Slicing-Aided Instance Segmentation**

If an anomaly is detected, the frame is split into overlapping $640 \\times 640$ patches using a sliding grid. Each patch is processed at its native resolution by our multi-class instance segmentation model, trained on a unified dataset compiled from **Dataset B (Car Parts)** and **Dataset C (CarDD\_COCO)**.

The bounding box coordinates of any predicted defects are normalized using the standard YOLO scaling format:

$$x\_{\\text{center}} \= \\frac{x\_{\\text{min}} \+ x\_{\\text{max}}}{2 \\cdot W}, \\quad w \= \\frac{x\_{\\text{max}} \- x\_{\\text{min}}}{W}$$
Polygons are reconstructed across patch boundaries using Non-Maximum Suppression (NMS).

### **Stage 3: Spatial Context Mapping**

Simultaneously, the global frame is evaluated by our panel segmenter model (trained on **Dataset A: Car Damages**). The coordinates of the detected defect polygon ($P\_{\\text{defect}}$) are checked against the panel segmentation masks ($M\_{\\text{panel}}$).

The system maps the defect to the panel that yields the highest intersection score:

$$\\text{Affected Panel} \= \\arg\\max\_{k} \\left( \\frac{\\text{Area}(P\_{\\text{defect}} \\cap M\_{\\text{panel}, k})}{\\text{Area}(P\_{\\text{defect}})} \\right)$$

### **Stage 4: Interactive Factory UI & Report Generation**

The dashboard UI processes the pipeline outputs to display:

* An overview image of the vehicle with colored defect overlays and panel boundaries.
* **Auto-generated close-up crops:** The system crops the image around the bounding box of each defect $\[x\_{\\text{min}}, y\_{\\text{min}}, x\_{\\text{max}}, y\_{\\text{max}}\]$ and displays these crops side-by-side with localized pixel dimensions.
* **Operator Queries:** Inspectors can use dropdown menus to filter results (e.g., displaying only the cropped images of scratches detected on the "Hood").

## **6\. Project Timeline (12-Week Schedule)**

| **Week** | **Phase** | **Key Activities & Milestones** |

| **1-2** | **Research & Design** | Literature review on SAHI and multi-stage models in manufacturing. Set up virtual environments (Python, PyTorch, Ultralytics). Design the pipeline's modular software architecture. |

| **3-5** | **Data Pipeline Engineering** | Develop data engineering scripts to parse Supervisely JSON schemas and COCO format polygons into a unified YOLO-compatible instance segmentation text format. Programmatically balance and augment under-represented classes (e.g., Corrosion/Paint chips). |

| **6-7** | **Multi-Model Training** | Train $M\_{\\text{binary}}$ (SOD), $M\_{\\text{core}}$ (Instance Segmentation), and $M\_{\\text{panel}}$ (Body Panels). Track model metrics ($\\text{mAP}@50$, $\\text{mAP}@50-95$, precision, recall) and plot validation loss curves. |

| **8-9** | **Pipeline & SAHI Integration** | Write the integration script to tile high-resolution inputs, run patch inference, merge overlapping edge polygons with NMS, and overlay defect coordinates onto the panel segmentation maps. |

| **10-11** | **Dashboard & Testing** | Build the interactive factory dashboard (Streamlit/Gradio). Connect image/video ingestion streams, implement cropping logic, add panel-filtering queries, and optimize the pipeline's processing speed. |

| **12** | **Documentation & Handover** | Write the final technical report, prepare presentation slides, package model weights, and hand over the codebase to the supervisor. |

## **7\. Expected Deliverables**

1. **Standardized Defect Dataset:** A unified dataset containing coordinated image-label directories formatted for YOLO instance segmentation.
2. **Suite of Trained Deep Learning Models:** Saved model weights (.pt files) for the binary pre-screener, the multi-class core engine, and the panel context mapper.
3. **Core Modular Codebase:** Clean, well-documented Python scripts driving training, inference, sliding-window patch slicing (SAHI), and coordinate merging.
4. **Industrial Factory Dashboard:** An interactive web dashboard allowing high-resolution frame processing, automatic crop generation, defect analysis, and panel-specific filtering.
5. **Technical Internship Report & Slide Deck:** A comprehensive final document detailing your technical findings, latency testing, and recommendations for future edge device deployments.

## **8\. Resources Required**

* **Hardware:** Access to an NVIDIA GPU (e.g., RTX 3080 / RTX 4090 or cloud instances via Colab/Kaggle) to train the three separate models.
* **Software:** Python 3.10+, PyTorch, Ultralytics YOLO framework, OpenCV, SAHI Python library, Streamlit or Gradio.
* **Data Core:** Supervisely Car Parts Dataset, Supervisely Car Damages Dataset, CarDD (COCO format), and CarDD (SOD format).

**Proposal Submitted By:** LOU Chumdararith

**Approved By:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ (Company Supervisor)

**Approved By:** \_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_ (Academic Advisor)
