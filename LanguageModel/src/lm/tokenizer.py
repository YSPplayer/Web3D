from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class CharTokenizer:
    name: str
    token_to_id: dict[str, int]
    id_to_token: dict[int, str]
    special_tokens: dict[str, int]

    @classmethod
    def from_file(cls, path: str | Path) -> "CharTokenizer":
        tokenizer_path = Path(path)
        raw = json.loads(tokenizer_path.read_text(encoding="utf-8"))

        token_to_id = {str(token): int(token_id) for token, token_id in raw["token_to_id"].items()}
        id_to_token = {int(token_id): str(token) for token_id, token in raw["id_to_token"].items()}
        special_tokens = {
            str(token): int(token_id)
            for token, token_id in raw["special_tokens"].items()
        }

        return cls(
            name=str(raw["name"]),
            token_to_id=token_to_id,
            id_to_token=id_to_token,
            special_tokens=special_tokens,
        )

    @property
    def vocab_size(self) -> int:
        return len(self.token_to_id)

    @property
    def pad_id(self) -> int:
        return self.special_tokens["<pad>"]

    @property
    def unk_id(self) -> int:
        return self.special_tokens["<unk>"]

    @property
    def bos_id(self) -> int:
        return self.special_tokens["<bos>"]

    @property
    def eos_id(self) -> int:
        return self.special_tokens["<eos>"]

    def encode(self, text: str) -> list[int]:
        ids: list[int] = []
        index = 0
        special_tokens = sorted(self.special_tokens, key=len, reverse=True)

        while index < len(text):
            matched_token = None
            for token in special_tokens:
                if text.startswith(token, index):
                    matched_token = token
                    break

            if matched_token is not None:
                ids.append(self.special_tokens[matched_token])
                index += len(matched_token)
                continue

            char = text[index]
            ids.append(self.token_to_id.get(char, self.unk_id))
            index += 1

        return ids

    def decode(self, ids: Iterable[int]) -> str:
        return "".join(self.id_to_token.get(int(token_id), "<unk>") for token_id in ids)

