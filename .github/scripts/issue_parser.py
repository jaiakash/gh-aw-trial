#!/usr/bin/env python3
"""AI Issue Analyzer - Validates and classifies issue titles for Kubeflow Pipelines."""

import os
import re
import subprocess
import sys


def validate_title_pattern(title, pattern=None):
    """
    Validate the issue title matches the required pattern.

    Args:
        title: The issue title to validate
        pattern: Optional regex pattern to use for validation

    Returns:
        tuple: (is_valid, issue_type, issue_area) where is_valid is bool
    """
    if pattern is None:
        pattern = r'^(bug|chore|feat)\(([a-z]+)\):\s*(\S.*)$'

    match = re.match(pattern, title)

    if not match:
        return False, None, None

    issue_type = match.group(1)
    issue_area = match.group(2)

    return True, issue_type, issue_area


def get_type_references(issue_type, repo):
    """
    Get reference standards based on issue type.

    Args:
        issue_type: The type of issue (bug, chore, feat)
        repo: The repository name (owner/repo format)

    Returns:
        str: Reference standard text or empty string
    """
    if repo == "kubeflow/pipelines":
        if issue_type == "bug":
            return "**Bug (#13180):** End-to-end test flakiness on Kubernetes 1.34 includes root cause analysis and environment data."

    return ""


def get_area_references(issue_area, repo):
    """
    Get reference standards based on issue area.

    Args:
        issue_area: The area of the issue (backend, frontend, sdk, etc.)
        repo: The repository name (owner/repo format)

    Returns:
        str: Reference standard text or empty string
    """
    if repo == "kubeflow/pipelines":
        area_references = {
            "backend": "**Backend (#13314):** S3 operations fail with non-AWS object stores after AWS SDK v2 checksum defaults change; the scope is clear and isolated.",
            "frontend": "**Frontend (#13108):** Frontend mock API startup and enum-drift coverage identifies explicit file paths and definitions of done.",
            "sdk": "**SDK (#12865):** set_accelerator_limit rejects valid accelerator counts and identifies the failing parameters precisely.",
        }
        return area_references.get(issue_area, "")

    return ""


def build_reference_standards(issue_type, issue_area, repo):
    """
    Build the complete reference standards string.

    Args:
        issue_type: The type of issue
        issue_area: The area of the issue
        repo: The repository name (owner/repo format)

    Returns:
        str: Combined reference standards
    """
    type_ref = get_type_references(issue_type, repo)
    area_ref = get_area_references(issue_area, repo)

    references = []
    if type_ref:
        references.append(type_ref)
    if area_ref:
        references.append(area_ref)

    if references:
        return " ".join(references)

    return "No directly comparable approved reference is available; evaluate only against the review rubric."


def post_invalid_title_comment(issue_number, repository):
    """
    Post a comment for an invalid issue title.

    Args:
        issue_number: The GitHub issue number
        repository: The GitHub repository (owner/repo format)
    """
    comment_body = (
        "## 🤖 AI Issue Quality Review\n\n"
        "⚠️ **Validation Failed:** Issue title must follow the correct format: "
        "`<type>(<area>): <title contents>`, where type is `bug`, `chore`, or `feat`."
    )

    subprocess.run(
        ["gh", "issue", "comment", str(issue_number), "--repo", repository, "--body", comment_body],
        check=True
    )


def write_github_output(key, value):
    """
    Write output to GitHub Actions output file.

    Args:
        key: The output key
        value: The output value
    """
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a") as f:
            f.write(f"{key}={value}\n")


def main():
    """Main execution function."""
    issue_title = os.environ.get("ISSUE_TITLE", "")
    issue_number = os.environ.get("ISSUE_NUMBER", "")
    github_repository = os.environ.get("GITHUB_REPOSITORY", "")
    title_pattern = os.environ.get("TITLE_PATTERN")
    repo = os.environ.get("REPO", github_repository)

    # Validate the title
    is_valid, issue_type, issue_area = validate_title_pattern(issue_title, title_pattern)

    if not is_valid:
        post_invalid_title_comment(issue_number, github_repository)
        write_github_output("valid", "false")
        return 0

    # Build reference standards
    reference_standards = build_reference_standards(issue_type, issue_area, repo)

    # Write outputs
    write_github_output("valid", "true")
    write_github_output("issue_type", issue_type)
    write_github_output("issue_area", issue_area)
    write_github_output("reference_standards", reference_standards)

    return 0


if __name__ == "__main__":
    sys.exit(main())
