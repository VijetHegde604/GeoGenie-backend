from transformers import CLIPProcessor, CLIPModel

def pre_download():
    model_id = "openai/clip-vit-base-patch32" 
    print(f"Pre-downloading {model_id}...")

    # These commands download the files and save them to the HF cache directory
    CLIPModel.from_pretrained(model_id)
    CLIPProcessor.from_pretrained(model_id)

    print("Download complete!")

if __name__ == "__main__":
    pre_download()
