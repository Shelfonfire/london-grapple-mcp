from mangum import Mangum
from server import mcp


def handler(event, context):
    # Reset session manager to avoid "can only be called once" error
    mcp._session_manager = None
    app = mcp.streamable_http_app()
    asgi_handler = Mangum(app, lifespan="auto")
    return asgi_handler(event, context)
