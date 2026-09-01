from wordassistant.cli import parser


REQUIRED = {
    "inspect",
    "context",
    "create",
    "edit",
    "table",
    "image",
    "section",
    "page-number",
    "field",
    "toc",
    "reference",
    "comment",
    "revision",
    "protect",
    "properties",
    "mail-merge",
    "verify",
    "render",
}


def _root_commands():
    action = next(action for action in parser()._actions if action.dest == "cmd")
    return set(action.choices)


def test_required_agent_command_families_are_exposed():
    assert REQUIRED <= _root_commands()


def test_every_required_family_has_help():
    for command in REQUIRED:
        try:
            parser().parse_args([command, "--help"])
        except SystemExit as exc:
            assert exc.code == 0


def test_verify_exposes_native_and_visual_completion_flags():
    args = parser().parse_args(
        [
            "verify",
            "report.docx",
            "--render",
            "--native-fields",
            "--visual-reviewed",
            "--visual-review-token",
            "abc123",
            "--delivery",
        ]
    )
    assert args.native_fields is True
    assert args.visual_reviewed is True
    assert args.visual_review_token == "abc123"
    assert args.delivery is True
