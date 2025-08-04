import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory
from typing import Generator

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

from tools.utils.file_utils import get_meta_data
from tools.utils.logger_utils import get_logger
from tools.utils.mimetype_utils import MimeType
from tools.utils.param_utils import get_md_text
from security import safe_command


class MarkdownToEpubTool(Tool):
    logger = get_logger(__name__)

    def _invoke(self, tool_parameters: dict) -> Generator[ToolInvokeMessage, None, None]:
        """
        invoke tools
        """
        # get parameters
        md_text = get_md_text(tool_parameters)

        current_script_folder = os.path.split(os.path.realpath(__file__))[0]

        try:
            with TemporaryDirectory(ignore_cleanup_errors=True, delete=True) as temp_md_dir:
                # skeleton resources
                shutil.copytree(
                    src=current_script_folder + "/mark2epub/skeleton",
                    dst=temp_md_dir,
                    dirs_exist_ok=True,
                )

                # markdown resources
                md_file_name = "markdown.md"
                Path(os.path.join(temp_md_dir, md_file_name)).write_text(md_text, encoding="utf-8")

                # description.json for mark2epub
                description_json = """
                {
                    "metadata":{
                        "dc:title":"Mark2Epub Sample",
                        "dc:creator":"md_exporter",
                        "dc:language":"en-US",
                        "dc:identifier":"mark2epub-sample",
                        "dc:source":"",
                        "meta":"",
                        "dc:date":"2025-01-01",
                        "dc:publisher":"",
                        "dc:contributor":"",
                        "dc:rights":"",
                        "dc:description":"",
                        "dc:subject":""
                        },
                    "default_css":["code_styles.css","general.css"],
                    "chapters":[
                                {"markdown":"markdown.md","css":""}
                            ]
                    }
                    """
                description_json_path = os.path.join(temp_md_dir, "description.json")
                Path(description_json_path).write_text(description_json, encoding="utf-8")

                # run mark2epub to convert md file to epub file
                with NamedTemporaryFile(suffix=".epub", delete=True) as temp_epub_file:
                    python_exec = sys.executable or "python3"
                    cmd = [python_exec, f"{current_script_folder}/mark2epub/mark2epub.py",
                           temp_md_dir,
                           temp_epub_file.name]
                    logging.info(cmd)

                    result = safe_command.run(subprocess.run, cmd,
                        timeout=60,  # timeout in seconds
                        capture_output=True,
                        text=True
                    )
                    if result.returncode != 0:
                        raise Exception(f"Failed to convert markdown text to EPUB file,"
                                        f" command: {" ".join(cmd)},"
                                        f" return code: {result.returncode},"
                                        f" stdout: {result.stdout},"
                                        f" error: {result.stderr}")
                    result_file_bytes = Path(temp_epub_file.name).read_bytes()

            yield self.create_blob_message(
                blob=result_file_bytes,
                meta=get_meta_data(
                    mime_type=MimeType.EPUB,
                    output_filename=tool_parameters.get("output_filename"),
                ),
            )

        except Exception as e:
            self.logger.exception("Failed to convert file")
            yield self.create_text_message(f"Failed to convert markdown text to Epub file, error: {str(e)}")
            return
