from __future__ import annotations

import torch
import torch.nn as nn
from transformers import AutoModel


class MultiHeadBackdoorModel(nn.Module):
    def __init__(self, base_model_name: str, num_labels_binary: int, num_labels_type: int) -> None:
        super().__init__()
        self.encoder = AutoModel.from_pretrained(base_model_name)
        hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(0.2)
        self.binary_head = nn.Linear(hidden, num_labels_binary)
        self.type_head = nn.Linear(hidden, num_labels_type)

    def forward(self, input_ids: torch.Tensor, attention_mask: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        cls = out.last_hidden_state[:, 0, :]
        cls = self.dropout(cls)
        return self.binary_head(cls), self.type_head(cls)
