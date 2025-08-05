from fastapi import FastAPI, HTTPException, Response, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import PlainTextResponse
from starlette.types import ASGIApp

from tools.md_to_docx.md_to_docx import MarkdownToDocxTool
from tools.md_to_html.md_to_html import MarkdownToHtmlTool
from tools.md_to_html_text.md_to_html_text import MarkdownToHtmlTextTool
from tools.md_to_pdf.md_to_pdf import MarkdownToPdfTool
from tools.md_to_png.md_to_png import MarkdownToPngTool
from tools.md_to_md.md_to_md import MarkdownToMarkdownTool
from tools.md_to_epub.md_to_epub import MarkdownToEpubTool
from tools.md_to_xml.md_to_xml import MarkdownToXmlTool
from tools.md_to_rst.md_to_rst import MarkdownToRstTool
from tools.md_to_pptx.md_to_pptx import MarkdownToPptxTool
from tools.md_to_codeblock.md_to_codeblock import MarkdownToCodeblockTool
from tools.md_to_xlsx.md_to_xlsx import MarkdownToXlsxTool
from tools.md_to_csv.md_to_csv import MarkdownToCsvTool
from tools.md_to_json.md_to_json import MarkdownToJsonTool
from tools.md_to_latex.md_to_latex import MarkdownToLatexTool

from dify_plugin.entities.tool import ToolInvokeMessage

app = FastAPI()


class ContentSizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, max_content_size: int):
        super().__init__(app)
        self.max_content_size = max_content_size

    async def dispatch(self, request, call_next):
        if request.method in ["POST", "PUT", "PATCH"]:
            content_length = request.headers.get("Content-Length")
            if content_length:
                try:
                    if int(content_length) > self.max_content_size:
                        return PlainTextResponse("Request entity too large", status_code=413)
                except ValueError:
                    pass
        response = await call_next(request)
        return response


MAX_MD_SIZE = 10 * 1024 * 1024  # 10 MB

app.add_middleware(ContentSizeLimitMiddleware, max_content_size=MAX_MD_SIZE)

security = HTTPBearer()

def authorize(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = os.getenv("API_TOKEN")
    if not token or credentials.credentials != token:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ConversionRequest(BaseModel):
    md_content: str
    conversion_to_format: str
    style: str | None = None


TOOL_MAP = {
    "md_to_docx": MarkdownToDocxTool,
    "md_to_html": MarkdownToHtmlTool,
    "md_to_html_text": MarkdownToHtmlTextTool,
    "md_to_pdf": MarkdownToPdfTool,
    "md_to_png": MarkdownToPngTool,
    "md_to_md": MarkdownToMarkdownTool,
    "md_to_epub": MarkdownToEpubTool,
    "md_to_xml": MarkdownToXmlTool,
    "md_to_rst": MarkdownToRstTool,
    "md_to_pptx": MarkdownToPptxTool,
    "md_to_codeblock": MarkdownToCodeblockTool,
    "md_to_xlsx": MarkdownToXlsxTool,
    "md_to_csv": MarkdownToCsvTool,
    "md_to_json": MarkdownToJsonTool,
    "md_to_latex": MarkdownToLatexTool,
}


@app.post("/convert")
def convert(req: ConversionRequest, _: HTTPAuthorizationCredentials = Depends(authorize)):
    md_size = len(req.md_content.encode("utf-8"))
    if md_size > MAX_MD_SIZE:
        raise HTTPException(status_code=413, detail="Markdown content too large")

    tool_cls = TOOL_MAP.get(req.conversion_to_format)
    if not tool_cls:
        raise HTTPException(status_code=400, detail="Unsupported conversion format")

    tool = tool_cls.from_credentials({})
    params = {"md_text": req.md_content}
    if req.style is not None:
        params["style"] = req.style

    try:
        for msg in tool.invoke(params):
            if msg.type == ToolInvokeMessage.MessageType.BLOB:
                blob = msg.message.blob
                meta = msg.meta or {}
                media_type = meta.get("mime_type", "application/octet-stream")
                headers = {}
                filename = meta.get("filename")
                if filename:
                    headers["Content-Disposition"] = f'attachment; filename="{filename}"'
                return Response(content=blob, media_type=media_type, headers=headers)
            elif msg.type == ToolInvokeMessage.MessageType.TEXT:
                media_type = "text/html" if req.conversion_to_format == "md_to_html_text" else "text/plain"
                return Response(content=msg.message.text, media_type=media_type)
        raise HTTPException(status_code=500, detail="No output generated")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
