import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from main import TOOL_MAP
from dify_plugin.entities.tool import ToolInvokeMessage


MD_TEXT = """# Hello

| A | B |
|---|---|
| 1 | 2 |
"""


def _run_tool(name: str, expect_blob: bool = True):
    cls = TOOL_MAP[name]
    inst = cls.from_credentials({})
    msgs = list(inst.invoke({"md_text": MD_TEXT}))
    if expect_blob:
        assert any(m.type == ToolInvokeMessage.MessageType.BLOB for m in msgs)
    else:
        assert any(m.type == ToolInvokeMessage.MessageType.TEXT for m in msgs)


def test_md_to_docx():
    _run_tool("md_to_docx")


def test_md_to_html():
    _run_tool("md_to_html")


def test_md_to_html_text():
    _run_tool("md_to_html_text", expect_blob=False)


def test_md_to_pdf():
    _run_tool("md_to_pdf")


def test_md_to_png():
    _run_tool("md_to_png")


def test_md_to_md():
    _run_tool("md_to_md")


def test_md_to_epub():
    _run_tool("md_to_epub")


def test_md_to_xml():
    _run_tool("md_to_xml")


def test_md_to_rst():
    _run_tool("md_to_rst")


def test_md_to_pptx():
    _run_tool("md_to_pptx")


def test_md_to_codeblock():
    _run_tool("md_to_codeblock")


def test_md_to_xlsx():
    _run_tool("md_to_xlsx")


def test_md_to_csv():
    _run_tool("md_to_csv")


def test_md_to_json():
    _run_tool("md_to_json")


def test_md_to_latex():
    _run_tool("md_to_latex")

