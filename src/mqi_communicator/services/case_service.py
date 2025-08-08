from typing import List, Optional
import os
from datetime import datetime

from mqi_communicator.domain.models import Case, CaseStatus
from mqi_communicator.domain.repositories.interfaces import ICaseRepository
from .interfaces import ICaseService

# A simple file system abstraction could be made for this
# For now, we use os directly.
class FileSystem:
    def list_directories(self, path: str) -> List[str]:
        """Returns a list of directory names in the given path."""
        try:
            return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
        except FileNotFoundError:
            return []

class CaseService(ICaseService):
    """
    Handles business logic related to Cases.
    """
    def __init__(self, case_repository: ICaseRepository, file_system: FileSystem, scan_path: str):
        self._repo = case_repository
        self._fs = file_system
        self._scan_path = scan_path

    def scan_for_new_cases(self) -> List[str]:
        """
        Scans the source directory for new cases and registers them.
        Returns a list of newly found case IDs.
        """
        found_dirs = self._fs.list_directories(self._scan_path)
        existing_case_ids = set(self._repo.get_all_case_ids())

        new_case_ids = [dir_name for dir_name in found_dirs if dir_name not in existing_case_ids]

        for case_id in new_case_ids:
            now = datetime.utcnow()
            new_case = Case(
                case_id=case_id,
                status=CaseStatus.NEW,
                beam_count=0, # This might be determined later
                created_at=now,
                updated_at=now,
                metadata={}
            )
            self._repo.save(new_case)

        return new_case_ids

    def get_case(self, case_id: str) -> Optional[Case]:
        """Retrieves a case by its ID."""
        return self._repo.get(case_id)

    def update_case_status(self, case_id: str, status: CaseStatus) -> None:
        """Updates the status of a case."""
        case = self._repo.get(case_id)
        if case:
            case.status = status
            case.updated_at = datetime.utcnow()
            self._repo.save(case)
        else:
            # Log that the case was not found
            # logger.warning(f"Attempted to update status of non-existent case: {case_id}")
            pass
