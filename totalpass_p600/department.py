from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from employees import Employees


@dataclass
class Department:
    name: str
    active: bool
    department_code: str
    in_revision_start_time: datetime
    in_revision_end_time: datetime
    out_revison_start_time: datetime
    out_revision_end_time: datetime
    employee_count: int = field(default=0)
    note: str = field(default="")
    employees: Employees = field(default_factory=Employees)
