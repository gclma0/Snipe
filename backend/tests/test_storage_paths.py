from app.storage.paths import candidate_document_path


def test_candidate_document_path_is_scoped_by_user_and_profile() -> None:
    path = candidate_document_path(
        "user-id",
        "profile-id",
        "../resume.pdf",
    )

    assert path == "user-id/profile-id/resume.pdf"
