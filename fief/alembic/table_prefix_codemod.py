import libcst as cst
from libcst.codemod import VisitorBasedCodemodCommand

from fief.models.base import TABLE_PREFIX_PLACEHOLDER


class ConvertTablePrefixStrings(VisitorBasedCodemodCommand):
    DESCRIPTION: str = (
        "Converts strings containing table prefix placeholder "
        "to a format-string with dynamic table prefix."
    )

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
