
import torch
from PIL import Image
from transformers import CLIPProcessor, CLIPModel
from typing import List, Tuple
from config import get_disease_labels

class WheatDiseaseCLIP:
    """Wrapper around CLIP for wheat disease classification."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32", device: str | None = None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.processor = CLIPProcessor.from_pretrained(model_name)

    @torch.no_grad()
    def predict(self, image: Image.Image, candidate_labels: List[str] | None = None) -> Tuple[str, float, List[Tuple[str, float]]]:
        """Classify an image into one of the candidate_labels using CLIP.

        Returns:
            best_label, best_score, all_scores_sorted
        """
        labels = candidate_labels or get_disease_labels()

        inputs = self.processor(
            text=[f"a photo of wheat leaf with {label}" if label != "Healthy" else "a photo of a healthy wheat leaf" for label in labels],
            images=image,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        outputs = self.model(**inputs)
        logits_per_image = outputs.logits_per_image  # shape: (1, num_labels)
        probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]

        scored = list(zip(labels, probs))
        scored.sort(key=lambda x: x[1], reverse=True)
        best_label, best_score = scored[0]
        return best_label, float(best_score), scored
