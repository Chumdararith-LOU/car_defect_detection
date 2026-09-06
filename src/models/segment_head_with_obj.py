"""Custom Segment26 head with an objectness branch for two-tier inference."""
import torch
import torch.nn as nn
from ultralytics.nn.modules.head import Segment26, Detect, Segment


class Segment26WithObjectness(Segment26):
    """Segment26 head + 1-channel objectness branch per scale level.
    
    Adds cv_obj: a lightweight 1x1 conv per FPN level that predicts
    'is there ANY defect here?' independent of class.
    """

    def __init__(self, nc=80, nm=32, npr=256, reg_max=16, end2end=False, ch=()):
        super().__init__(nc, nm, npr, reg_max, end2end, ch)
        for attr in ('f', 'i', 'type', 'args'):
            if not hasattr(self, attr):
                setattr(self, attr, getattr(super(), attr, None))
        # Objectness branch: 1x1 conv per scale level, 1 output channel
        self.cv_obj = nn.ModuleList(nn.Conv2d(x, 1, 1) for x in ch)
        
        # Initialize with small weights and a negative bias so initial 
        # predictions favor background (prevents early training instability)
        for m in self.cv_obj:
            nn.init.constant_(m.weight, 0.0)
            nn.init.constant_(m.bias, -2.0) 

    def forward(self, x):
        """Forward pass adding objectness logits to the preds dict."""
        bs = x[0].shape[0]
        
        # Compute objectness logits early: (bs, 1, total_anchors)
        obj_logits = torch.cat(
            [self.cv_obj[i](x[i]).view(bs, 1, -1) for i in range(self.nl)], dim=-1
        )

        try:
            # Attempt to use the parent class's forward method.
            # In your specific Ultralytics fork, Segment26.forward works for training 
            # (returning a dict with 'bbox', 'cls', etc.) but crashes during inference 
            # because it incorrectly calls Detect.forward() which omits cv4 (mask coefficients).
            outputs = super().forward(x)
        except RuntimeError as e:
            if "split_with_sizes" in str(e) and not self.training:
                # Fallback to the standard Segment.forward for inference to properly handle cv4
                outputs = Segment.forward(self, x)
            else:
                raise e

        # Attach objectness logits onto whichever dict actually carries the raw
        # preds, in BOTH training and eval mode. This matters because Ultralytics
        # computes validation loss by running the model in eval() mode
        # (self.training is False) but still needs a preds structure compatible
        # with the loss criterion — if "obj" were only injected when
        # self.training, validation-time loss_items comes back one element
        # shorter than training-time loss_items, and the trainer's
        # preallocated loss accumulator (sized from a training batch) mismatches
        # it at the end of the first epoch.
        obj_target_dict = None
        if isinstance(outputs, dict):
            obj_target_dict = outputs
        elif isinstance(outputs, tuple) and len(outputs) == 2 and isinstance(outputs[1], dict):
            obj_target_dict = outputs[1]
        if obj_target_dict is not None:
            obj_target_dict["obj"] = obj_logits

        if self.training:
            # Inject objectness logits into the training dict expected by your patched loss
            if isinstance(outputs, dict):
                if "proto" not in outputs and hasattr(self, "proto"):
                    outputs["proto"] = self._get_or_compute_proto(x, outputs)
            elif isinstance(outputs, tuple):
                # Fallback if it returned a tuple instead of a dict
                y, p = outputs if len(outputs) == 2 else (outputs[0], None)
                outputs = {"preds": y, "proto": p, "obj": obj_logits}
            return outputs

        # --- INFERENCE MODE ---
        if isinstance(outputs, tuple):
            preds, proto = outputs
        else:
            preds = outputs
            proto = None

        # Apply two-tier objectness gating directly to the decoded predictions
        if isinstance(preds, torch.Tensor) and preds.dim() == 3:
            nc = self.nc
            # Convert objectness logits to probabilities and reshape for broadcasting: (bs, N, 1)
            obj_probs = obj_logits.transpose(1, 2).sigmoid()
            
            # Multiply the class scores (indices 4 to 4+nc) by the objectness probability
            # This acts as your two-tier gating: final_score = P(class) * P(object)
            preds[:, :, 4 : 4 + nc] = preds[:, :, 4 : 4 + nc] * obj_probs

        # Return standard Ultralytics Segment inference format: (decoded_preds, proto)
        return preds, proto

    def _get_or_compute_proto(self, x, outputs):
        """Recover 'proto' when stock Segment26.forward() didn't put it at the
        top level of the preds dict.

        Two known reasons this key can be missing, per Ultralytics'
        Segment26.forward source:

        1. end2end models: proto is nested under outputs['one2many']['proto']
           / outputs['one2one']['proto'] instead of a top-level key.
        2. Some other path skipped proto assignment entirely — as a last
           resort, replicate Segment26.forward's own call exactly. Proto26
           (self.proto here) fuses the FULL multi-scale feature pyramid
           internally (base level + refined/upsampled higher levels), so it
           must be called with the whole list `x`, never a single x[i].
        """
        one2many = outputs.get("one2many")
        if isinstance(one2many, dict) and "proto" in one2many:
            return one2many["proto"]

        # Matches Segment26.forward()'s own `proto = self.proto(x)` call.
        # Note: with the semantic-segmentation head enabled, Proto26 returns
        # a (mask_protos, semantic_logits) tuple during training, exactly as
        # stock Segment26.forward stores it — check whether your patched
        # loss expects that tuple or a bare tensor under "proto".
        return self.proto(x)

    def fuse(self):
        """Remove heads for inference optimization."""
        super().fuse()
        # Keep cv_obj for inference (needed for two-tier gating)