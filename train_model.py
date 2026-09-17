from ultralytics import YOLO

def main():
    print("=== EleGuard AI - Model Training Pipeline ===")
    
    # Load base weights
    model = YOLO("yolov8n.pt")

    # Start fine-tuning on Sri Lankan wild elephant data
    model.train(
        data="data.yaml",
        epochs=15,             # 15 epochs gives high convergence on transfer learning
        imgsz=640,             # Standard detection resolution
        batch=8,               # Balanced for laptop CPU/GPU stability
        device="cpu",          # Set to 0 if an NVIDIA GPU is available
        workers=2,
        project="corridor_model",
        name="custom_elephant",
        exist_ok=True
    )

    print("\n[+] Training complete!")
    print("[+] Best weights saved at: corridor_model/custom_elephant/weights/best.pt")

if __name__ == "__main__":
    main()
