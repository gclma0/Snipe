from pathlib import PurePosixPath
from uuid import UUID


def candidate_document_path(user_id: UUID | str, profile_id: UUID | str, filename: str) -> str:
    clean_name = PurePosixPath(filename).name
    if not clean_name:
        raise ValueError("filename must include a basename")
    return str(PurePosixPath(str(user_id), str(profile_id), clean_name))
