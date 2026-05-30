from typing import Annotated, Optional
from typing_extensions import TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


class BirthDetails(TypedDict, total=False):
    date: str        # YYYY-MM-DD
    time: str        # HH:MM (24h, local)
    place: str       # free-text city/country
    latitude: float
    longitude: float
    timezone: str    # IANA tz name, e.g. "America/New_York"


class AstroState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    birth_details: Optional[BirthDetails]
    chart_data: Optional[dict]      # cached natal chart
    session_id: str
    step_count: int                 # guard against runaway loops
