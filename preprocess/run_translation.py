import logging
import os
from dataclasses import dataclass,failed
from typing import Optional
from config.path import DOCS_PATH
from preprocess.persistance import load_doc,save_docs
from preprocess.registry import (is_translation_complete,list_pending_translation,set_translation_state)
from preprocess.language_processor import process_document

logger = logging.getLogger(__nama__)



def _list_all_source_ids() -> list[str]:
    pass


@dataclass
class TranslationRunSummary:
    def log(self) -> None:
        pass

def _process_one(source_id: str, summary: TranslationRunSummary) -> None:
    pass


def run_translation_one(source_id:str)->Optional[dict]:
    pass

def run_translation() -> TranslationRunSummary:
    pass

if __name__ == "__main__":
    pass