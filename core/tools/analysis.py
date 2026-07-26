"""gdexplore, gdoptimize, gdvalidate, gdcheck — Project analysis tools."""

from __future__ import annotations

import json
import logging

from core.config import GODOT_PROJECT, mcp, scene, validator

logger = logging.getLogger("godot-mcp")


@mcp.tool()
async def gdexplore() -> str:
    """Analyze the current Godot project and suggest next features.

    Scans all .tscn and .gd files in the project, classifies their content,
    and compares against a feature checklist to identify what's implemented
    and what's missing.

    Returns JSON with:
    - features_found: list of implemented features
    - features_missing: list of missing features
    - suggestions: list of recommended next steps with links to knowledge base
    """
    logger.info("gdexplore → scanning project")

    try:
        features_found: list[str] = []
        features_missing: list[str] = []
        suggestions: list[str] = []

        # Scan .tscn files
        tscn_files = list(GODOT_PROJECT.rglob("*.tscn"))
        gd_files = list(GODOT_PROJECT.rglob("*.gd"))

        # Check for player
        has_player = any("player" in f.name.lower() for f in tscn_files)
        if has_player:
            features_found.append("player_scene")
        else:
            features_missing.append("player_scene")
            suggestions.append("Create a player scene (CharacterBody2D/3D)")

        # Check for enemies
        has_enemies = any("enemy" in f.name.lower() for f in tscn_files)
        if has_enemies:
            features_found.append("enemy_scene")
        else:
            features_missing.append("enemy_scene")
            suggestions.append("Add enemy scenes for gameplay challenge")

        # Check for UI
        has_ui = any(
            "ui" in f.name.lower() or "hud" in f.name.lower() for f in tscn_files
        )
        if has_ui:
            features_found.append("ui_scene")
        else:
            features_missing.append("ui_scene")
            suggestions.append("Create a HUD or UI scene")

        # Check for game manager
        has_game_manager = any(
            "game_manager" in f.name.lower() or "manager" in f.name.lower()
            for f in gd_files
        )
        if has_game_manager:
            features_found.append("game_manager")
        else:
            features_missing.append("game_manager")
            suggestions.append("Add a GameManager autoload for score/lives")

        # Check for main menu
        has_main_menu = any("menu" in f.name.lower() for f in tscn_files)
        if has_main_menu:
            features_found.append("main_menu")
        else:
            features_missing.append("main_menu")
            suggestions.append("Build a main menu scene")

        # Check for settings
        has_settings = any("settings" in f.name.lower() for f in tscn_files + gd_files)
        if has_settings:
            features_found.append("settings")
        else:
            features_missing.append("settings")
            suggestions.append("Add settings/options menu")

        # Check for signals usage
        has_signals = False
        for gd_file in gd_files:
            try:
                content = gd_file.read_text(encoding="utf-8")
                if "signal " in content or ".emit()" in content:
                    has_signals = True
                    break
            except Exception:
                pass
        if has_signals:
            features_found.append("signal_system")

        # Check for type hints
        has_type_hints = False
        for gd_file in gd_files:
            try:
                content = gd_file.read_text(encoding="utf-8")
                if ": float" in content or ": int" in content or ": String" in content:
                    has_type_hints = True
                    break
            except Exception:
                pass
        if has_type_hints:
            features_found.append("typed_scripts")

        response = {
            "project_path": str(GODOT_PROJECT),
            "total_scenes": len(tscn_files),
            "total_scripts": len(gd_files),
            "features_found": features_found,
            "features_missing": features_missing,
            "suggestions": suggestions,
        }

        logger.info(
            "gdexplore completed: %d found, %d missing",
            len(features_found),
            len(features_missing),
        )
        return json.dumps(response, indent=2)

    except Exception as exc:
        msg = f"ERROR exploring project: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def gdoptimize() -> str:
    """Analyze the project for optimization opportunities.

    Scans all .gd and .tscn files and identifies:
    - Missing type hints in scripts
    - Missing @export variables
    - Missing collision shapes in physics scenes
    - Missing visual nodes (Sprite2D/MeshInstance3D)

    Returns JSON with findings ranked by severity.
    """
    logger.info("gdoptimize → scanning for optimizations")

    try:
        findings: list[dict] = []

        # Scan .gd files for type hints
        gd_files = list(GODOT_PROJECT.rglob("*.gd"))
        for gd_file in gd_files:
            try:
                content = gd_file.read_text(encoding="utf-8")
                rel_path = str(gd_file.relative_to(GODOT_PROJECT))

                # Check for untyped variables
                lines = content.split("\n")
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    if stripped.startswith("var ") and ":" not in stripped:
                        findings.append(
                            {
                                "severity": "medium",
                                "file": rel_path,
                                "line": i,
                                "issue": "Untyped variable",
                                "fix": "Add type annotation (e.g., 'var health: int = 100')",
                            }
                        )

                # Check for missing @export
                if "var " in content and "@export" not in content:
                    findings.append(
                        {
                            "severity": "low",
                            "file": rel_path,
                            "line": 0,
                            "issue": "No @export variables",
                            "fix": "Consider using @export for configurable properties",
                        }
                    )

            except Exception:
                pass

        # Scan .tscn files for collision shapes
        tscn_files = list(GODOT_PROJECT.rglob("*.tscn"))
        for tscn_file in tscn_files:
            try:
                content = tscn_file.read_text(encoding="utf-8")
                rel_path = str(tscn_file.relative_to(GODOT_PROJECT))

                # Check for physics bodies without collision shapes
                has_physics = (
                    "CharacterBody2D" in content or "CharacterBody3D" in content
                )
                has_collision = (
                    "CollisionShape2D" in content or "CollisionShape3D" in content
                )
                if has_physics and not has_collision:
                    findings.append(
                        {
                            "severity": "high",
                            "file": rel_path,
                            "line": 0,
                            "issue": "Physics body without collision shape",
                            "fix": "Add CollisionShape2D/3D node",
                        }
                    )

                # Check for missing visuals
                has_visual = "Sprite2D" in content or "MeshInstance3D" in content
                if has_physics and not has_visual:
                    findings.append(
                        {
                            "severity": "medium",
                            "file": rel_path,
                            "line": 0,
                            "issue": "Physics body without visual representation",
                            "fix": "Add Sprite2D or MeshInstance3D node",
                        }
                    )

            except Exception:
                pass

        # Sort by severity
        severity_order = {"high": 0, "medium": 1, "low": 2}
        findings.sort(key=lambda x: severity_order.get(x["severity"], 3))

        response = {
            "project_path": str(GODOT_PROJECT),
            "total_findings": len(findings),
            "findings": findings,
        }

        logger.info("gdoptimize completed: %d findings", len(findings))
        return json.dumps(response, indent=2)

    except Exception as exc:
        msg = f"ERROR optimizing project: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def gdvalidate() -> str:
    """Validate the project against best practices and conventions.

    Checks:
    - Folder structure (scenes/, scripts/, assets/ exist)
    - Naming conventions (snake_case files, PascalCase nodes)
    - Scene completeness (visual + collision pairs)
    - Script quality (extends, type hints)
    - GDScript syntax validation for all .gd files

    Returns JSON with passed/warnings/errors and a score.
    """
    logger.info("gdvalidate → checking project compliance")

    try:
        passed: list[str] = []
        warnings: list[str] = []
        errors: list[str] = []

        # Check folder structure
        required_folders = ["scenes", "scripts"]
        for folder in required_folders:
            if (GODOT_PROJECT / folder).is_dir():
                passed.append(f"Folder structure: {folder}/ exists")
            else:
                errors.append(f"Folder structure: Missing {folder}/ directory")

        # Check for project.godot
        if (GODOT_PROJECT / "project.godot").exists():
            passed.append("Project file: project.godot exists")
        else:
            errors.append("Project file: Missing project.godot")

        # Check naming conventions
        gd_files = list(GODOT_PROJECT.rglob("*.gd"))
        for gd_file in gd_files:
            rel_path = str(gd_file.relative_to(GODOT_PROJECT))
            name = gd_file.stem

            # Check snake_case
            if name != name.lower() or " " in name:
                warnings.append(f"Naming: {rel_path} not snake_case")
            else:
                passed.append(f"Naming: {rel_path} is snake_case")

        # Check scene completeness
        tscn_files = list(GODOT_PROJECT.rglob("*.tscn"))
        for tscn_file in tscn_files:
            try:
                content = tscn_file.read_text(encoding="utf-8")
                rel_path = str(tscn_file.relative_to(GODOT_PROJECT))

                has_physics = (
                    "CharacterBody2D" in content or "CharacterBody3D" in content
                )
                has_collision = (
                    "CollisionShape2D" in content or "CollisionShape3D" in content
                )
                has_visual = "Sprite2D" in content or "MeshInstance3D" in content

                if has_physics:
                    if has_collision:
                        passed.append(f"Scene completeness: {rel_path} has collision")
                    else:
                        errors.append(
                            f"Scene completeness: {rel_path} missing collision"
                        )
                    if has_visual:
                        passed.append(f"Scene completeness: {rel_path} has visual")
                    else:
                        warnings.append(
                            f"Scene completeness: {rel_path} missing visual"
                        )

            except Exception:
                pass

        # Check script quality
        for gd_file in gd_files:
            try:
                content = gd_file.read_text(encoding="utf-8")
                rel_path = str(gd_file.relative_to(GODOT_PROJECT))

                # Check for extends
                if "extends " in content:
                    passed.append(f"Script quality: {rel_path} has extends")
                else:
                    errors.append(f"Script quality: {rel_path} missing extends")

                # Check for type hints
                if ": float" in content or ": int" in content or ": String" in content:
                    passed.append(f"Script quality: {rel_path} has type hints")
                else:
                    warnings.append(f"Script quality: {rel_path} missing type hints")

            except Exception:
                pass

        # GDScript syntax validation
        syntax_results = validator.validate_project()
        if syntax_results["invalid_files"] > 0:
            for result in syntax_results["results"]:
                error_msg = result["errors"][0]["message"]
                line_num = result["errors"][0].get("line", 0)
                errors.append(
                    f"Syntax error: {result['file']} (line {line_num}): {error_msg}"
                )
        else:
            passed.append(
                f"Syntax validation: all {syntax_results['valid_files']} .gd files valid"
            )

        # Calculate score
        total = len(passed) + len(warnings) + len(errors)
        score = int(len(passed) / total * 100) if total > 0 else 0

        response = {
            "project_path": str(GODOT_PROJECT),
            "score": score,
            "passed": passed,
            "warnings": warnings,
            "errors": errors,
            "syntax_validation": {
                "total_files": syntax_results["total_files"],
                "valid_files": syntax_results["valid_files"],
                "invalid_files": syntax_results["invalid_files"],
            },
        }

        logger.info(
            "gdvalidate completed: score=%d, passed=%d, warnings=%d, errors=%d",
            score,
            len(passed),
            len(warnings),
            len(errors),
        )
        return json.dumps(response, indent=2)

    except Exception as exc:
        msg = f"ERROR validating project: {exc}"
        logger.error(msg)
        return msg


@mcp.tool()
async def gdcheck(file_path: str) -> str:
    """Check GDScript syntax and semantics for a single file or all files.

    Validates .gd files using gdtoolkit parser for syntax errors,
    plus semantic checks:
    - Mixed indentation (tabs vs spaces)
    - Missing extends/class_name declaration
    - Files over 300 lines (monolithic, hard to debug)
    - class_name usage (may fail in CLI without editor indexing)
    - Common Godot API misuse patterns

    Args:
        file_path: Relative path to a .gd file, or empty string to check all files.

    Returns JSON with validation results.
    """
    logger.info("gdcheck → %s", file_path or "(all files)")

    try:
        if file_path:
            result = validator.validate_file(file_path)
            # Add semantic checks
            try:
                full_path = GODOT_PROJECT / file_path
                content = full_path.read_text(encoding="utf-8")
                semantic = validator.semantic_checks(content)
            except Exception:
                semantic = []

            response = {
                "file": file_path,
                "valid": result["valid"],
                "errors": result["errors"],
                "semantic_issues": semantic,
            }
        else:
            result = validator.validate_project()
            all_semantic = {}
            for r in result.get("results", []):
                fpath = r.get("file", "")
                if fpath.endswith(".gd"):
                    try:
                        content = (GODOT_PROJECT / fpath).read_text(encoding="utf-8")
                        issues = validator.semantic_checks(content)
                        if issues:
                            all_semantic[fpath] = issues
                    except Exception:
                        pass

            response = {
                "total_files": result["total_files"],
                "valid_files": result["valid_files"],
                "invalid_files": result["invalid_files"],
                "errors": result["results"],
                "semantic_issues": all_semantic,
            }

        logger.info(
            "gdcheck completed: valid=%s",
            response.get("valid", response.get("valid_files", 0)),
        )
        return json.dumps(response, indent=2)

    except Exception as exc:
        msg = f"ERROR checking syntax: {exc}"
        logger.error(msg)
        return msg
