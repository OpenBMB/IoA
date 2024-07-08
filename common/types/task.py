from pydantic import BaseModel


class TaskInfo(BaseModel):
    comm_id: str
    goal: str
    teammates: list[str]
    created_at: str
