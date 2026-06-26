from pydantic import BaseModel, Field

class ExecutorConfig(BaseModel):
    max_concurrent_sagas: int = Field(default=10)
    saga_timeout_seconds: int = Field(default=3600)
