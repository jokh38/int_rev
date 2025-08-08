from typing import List, Optional

from mqi_communicator.domain.models import Case, Job
from mqi_communicator.domain.repositories.interfaces import ICaseRepository, IJobRepository
from mqi_communicator.infrastructure.state.interfaces import IStateManager

# Pydantic is often used for this to handle the dict -> model conversion robustly.
# Since I can't add dependencies and test, I'll do a manual conversion.
# This assumes the data in the state manager is already dict-serialized.
def _dict_to_model(model_class, data):
    if data is None:
        return None
    return model_class(**data)

class CaseRepository(ICaseRepository):
    """
    A repository for Cases that persists data to a JSON file via a StateManager.
    """
    def __init__(self, state_manager: IStateManager):
        self._sm = state_manager
        # Ensure the 'cases' key exists in the state
        with self._sm.transaction() as tx:
            state = tx.get_state()
            if "cases" not in state:
                state["cases"] = {}

    def save(self, case: Case) -> None:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            state["cases"][case.case_id] = case.model_dump(mode='json')

    def get(self, case_id: str) -> Optional[Case]:
        # Get is read-only, so a transaction isn't strictly necessary
        # but using it ensures we get a consistent view of the state.
        with self._sm.transaction() as tx:
            state = tx.get_state()
            case_data = state["cases"].get(case_id)
            return _dict_to_model(Case, case_data)

    def get_all(self) -> List[Case]:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            return [_dict_to_model(Case, data) for data in state["cases"].values()]

    def get_all_case_ids(self) -> List[str]:
        with self._sm.transaction() as tx:
            return list(tx.get_state()["cases"].keys())


class JobRepository(IJobRepository):
    """
    A repository for Jobs that persists data to a JSON file via a StateManager.
    """
    def __init__(self, state_manager: IStateManager):
        self._sm = state_manager
        # Ensure the 'jobs' key exists in the state
        with self._sm.transaction() as tx:
            state = tx.get_state()
            if "jobs" not in state:
                state["jobs"] = {}

    def save(self, job: Job) -> None:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            state["jobs"][job.job_id] = job.model_dump(mode='json')

    def get(self, job_id: str) -> Optional[Job]:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            job_data = state["jobs"].get(job_id)
            return _dict_to_model(Job, job_data)

    def get_all(self) -> List[Job]:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            return [_dict_to_model(Job, data) for data in state["jobs"].values()]

    def find_by_case_id(self, case_id: str) -> List[Job]:
        with self._sm.transaction() as tx:
            state = tx.get_state()
            return [
                _dict_to_model(Job, data)
                for data in state["jobs"].values()
                if data["case_id"] == case_id
            ]
