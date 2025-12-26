
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
    def is_wheat_image(self, image: Image.Image, threshold: float = 0.3) -> Tuple[bool, float]:
        """Check if the image is wheat-related before disease classification.
        
        Args:
            image: Input image
            threshold: Minimum confidence threshold to consider image as wheat-related
            
        Returns:
            (is_wheat, confidence_score)
        """
        # Compare against wheat and non-wheat descriptions
        wheat_descriptions = [
            "a photo of a wheat plant",
            "a photo of wheat leaves",
            "a photo of wheat leaf",
            "a photo of wheat crop",
            "a photo of wheat field",
        ]
        
        non_wheat_descriptions = [
            "a photo of an animal",
            "a photo of a pet",
            "a photo of a cat",
            "a photo of a dog",
            "a photo of a person",
            "a photo of food",
            "a photo of a building",
            "a photo of a car",
            "a photo of nature without plants",
        ]
        
        all_descriptions = wheat_descriptions + non_wheat_descriptions
        
        inputs = self.processor(
            text=all_descriptions,
            images=image,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        outputs = self.model(**inputs)
        logits_per_image = outputs.logits_per_image  # shape: (1, num_descriptions)
        probs = logits_per_image.softmax(dim=1).cpu().numpy()[0]
        
        # Get the maximum probability for wheat descriptions
        wheat_probs = probs[:len(wheat_descriptions)]
        max_wheat_prob = float(wheat_probs.max())
        
        # Get the maximum probability for non-wheat descriptions
        non_wheat_probs = probs[len(wheat_descriptions):]
        max_non_wheat_prob = float(non_wheat_probs.max())
        
        # Consider it wheat if wheat probability is significantly higher
        is_wheat = max_wheat_prob > threshold and max_wheat_prob > max_non_wheat_prob
        confidence = max_wheat_prob
        
        return is_wheat, confidence

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
