import json
from pathlib import Path

from fastapi.templating import Jinja2Templates
from markupsafe import Markup

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent / "templates"))
templates.env.filters["tojson"] = lambda value: Markup(json.dumps(value))
