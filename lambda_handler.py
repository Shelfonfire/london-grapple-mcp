from mangum import Mangum
from server import mcp

app = mcp.streamable_http_app()
handler = Mangum(app, lifespan="auto")
