import argparse
import sys
from typing import IO

import libcst as cst
from libcst.codemod import (
    CodemodContext,
    ContextAwareTransformer,
    TransformSuccess,
    transform_module,
)

from fief.models.base import TABLE_PREFIX_PLACEHOLDER


class ConvertTablePrefixStrings(ContextAwareTransformer):
    def leave_SimpleString(
        self, original_node: cst.SimpleString, updated_node: cst.SimpleString
    ) -> cst.SimpleString | cst.FormattedString:
        value = updated_node.evaluated_value

        if not isinstance(value, str):
            return updated_node

        if TABLE_PREFIX_PLACEHOLDER in value:
            before, after = value.split(TABLE_PREFIX_PLACEHOLDER)
            before = before.replace('"', '\\"')
            after = after.replace('"', '\\"')
            return cst.FormattedString(
                [
                    cst.FormattedStringText(before),
                    cst.FormattedStringExpression(cst.Name("table_prefix")),
                    cst.FormattedStringText(after),
                ]
            )

        return updated_node


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "file", help="The file to transform", type=argparse.FileType("r+")
    )
    args = parser.parse_args()
    file: IO = args.file

    context = CodemodContext()
    result = transform_module(ConvertTablePrefixStrings(context), file.read())

    if not isinstance(result, TransformSuccess):
        print(f"Error: {result}")
        sys.exit(1)

    file.seek(0)
    file.write(result.code)
