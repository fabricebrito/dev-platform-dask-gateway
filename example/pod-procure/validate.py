# pip install cwltool==3.1.20250110105449

from cwltool.main import main as cwlmain
from cwltool.process import use_custom_schema
import argparse
from io import StringIO
import cwltool
import re

# with open("schema.yaml") as f:
#     schema_content = f.read()

# use_custom_schema("v1.2", "https://calrissian-cwl.github.io/#", schema_content)

def add_arv_hints():
    cwltool.command_line_tool.ACCEPTLIST_EN_RELAXED_RE = re.compile(r".*")
    cwltool.command_line_tool.ACCEPTLIST_RE = cwltool.command_line_tool.ACCEPTLIST_EN_RELAXED_RE
    supported_versions = ["v1.0", "v1.1", "v1.2"]
    
    with open("schema.yaml") as f:
        schema_content = f.read()
    
    for s in supported_versions:
        use_custom_schema(s, "https://calrissian-cwl.github.io/#", schema_content)
    
    cwltool.process.supportedProcessRequirements.extend([
        "https://calrissian-cwl.github.io/#DaskGatewayRequirement"
    ])

add_arv_hints()

parsed_args = argparse.Namespace(
    validate=True,
    fast_parser=False,
    enable_ext=True,
    workflow="example.cwl",
    custom_schema_callback=add_arv_hints,
)

stream_out = StringIO()
stream_err = StringIO()

res = cwlmain(
    args=parsed_args,
    stdout=stream_out,
)

print(stream_out.getvalue())