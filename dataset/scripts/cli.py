"""CLI wizard for managing Biblioperson profiles and jobs.
Author: Biblioperson
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# optional dependency
try:
    import questionary
except ImportError:
    questionary = None  # type: ignore

from .utils import OPS  # rule‑engine operators

logger = logging.getLogger("biblioperson.cli")
logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_DIR = SCRIPT_DIR.parent / "config"
SCHEMA_DIR = CONFIG_DIR / "schema"

CONTENT_PROFILES_PATH = CONFIG_DIR / "content_profiles.json"
JOBS_CONFIG_PATH = CONFIG_DIR / "jobs_config.json"
CONTENT_PROFILES_SCHEMA = json.loads((SCHEMA_DIR / "content_profiles.schema.json").read_text())
JOBS_CONFIG_SCHEMA = json.loads((SCHEMA_DIR / "jobs_config.schema.json").read_text())

# --------------------------------------------------------------------------- #
#                                   helpers                                   #
# --------------------------------------------------------------------------- #

def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        save_json(path, default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        logger.error("Invalid JSON in %s: %s", path, err)
        sys.exit(1)

def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Saved %s", path.name)

def ask(prompt: str, default: str | None = None, *, validate: str | None = None) -> str:
    if questionary:
        q = questionary.text(prompt, default=default)
        if validate:
            q = q.validate(lambda x: bool(re.match(validate, x)) or "Invalid format")
        return q.ask()
    while True:
        raw = input(f"{prompt} [{default or ''}]: ").strip() or (default or "")
        if not validate or re.match(validate, raw):
            return raw
        print("Invalid format – try again.")

def yes_no(prompt: str, *, default: bool = False) -> bool:
    d = "y" if default else "n"
    resp = ask(f"{prompt} [y/n]", default=d, validate=r"^[yYnN]$")
    return resp.lower() == "y"

def menu_choice(title: str, options: List[str], *, default: str | None = None) -> str:
    if questionary:
        return questionary.select(title, choices=options, default=default).ask()
    print(f"\n{title}")
    for i, opt in enumerate(options, 1):
        print(f"  {i}. {opt}")
    while True:
        sel = input("Select option #: ").strip()
        if sel.isdigit() and 1 <= int(sel) <= len(options):
            return options[int(sel) - 1]

# --------------------------------------------------------------------------- #
#                         filter‑rule interactive wizard                      #
# --------------------------------------------------------------------------- #

def ask_filter_rules() -> Optional[List[Dict[str, Any]]]:
    if not yes_no("Add filtering rules for this JSON job?", default=False):
        return None
    rules: List[Dict[str, Any]] = []
    while True:
        path = ask("JSON path (dot‑notation):")
        op = menu_choice("Operator", list(OPS.keys()))
        value_str = ask("Value (will auto‑cast bool/num/null if possible):")
        try:
            value = json.loads(value_str)
        except Exception:
            value = value_str
        exclude = yes_no("Exclude when rule PASSES?", default=False)
        rules.append({"path": path, "op": op, "value": value, "exclude": exclude})
        if not yes_no("Add another rule?", default=False):
            break
    return rules or None

# --------------------------------------------------------------------------- #
#                          profile management functions                       #
# --------------------------------------------------------------------------- #

def menu_profiles(profiles: Dict[str, Any]) -> Dict[str, Any]:
    while True:
        choice = menu_choice("Content profiles", ["Create", "Edit", "Delete", "Back"])
        if choice == "Create":
            profiles = create_profile(profiles)
        elif choice == "Edit":
            profiles = edit_profile(profiles)
        elif choice == "Delete":
            profiles = delete_profile(profiles)
        else:
            return profiles

def create_profile(profiles: Dict[str, Any]) -> Dict[str, Any]:
    pid = ask("Internal profile ID (snake‑case):", validate=r"^[a-z0-9_-]+$")
    if pid in profiles:
        logger.warning("Profile %s already exists", pid)
        return profiles
    display = ask("Display name:", default=pid)
    group = menu_choice("Source format group", ["json_like", "document", "presentation"])
    chunk = ask("Default chunking strategy (class name):", default="ParagraphChunkerStrategy")
    profiles[pid] = {
        "profile_display_name": display,
        "source_format_group": group,
        "content_kind": "generic",
        "chunking_strategy_name": chunk,
    }
    logger.info("Profile %s created", pid)
    return profiles

def select_profile(profiles: Dict[str, Any]) -> str | None:
    if not profiles:
        logger.warning("No profiles available")
        return None
    opt = menu_choice("Choose profile", list(profiles.keys()) + ["Cancel"])
    return None if opt == "Cancel" else opt

def edit_profile(profiles: Dict[str, Any]) -> Dict[str, Any]:
    pid = select_profile(profiles)
    if not pid:
        return profiles
    prof = profiles[pid]
    prof["profile_display_name"] = ask("Display name:", default=prof.get("profile_display_name"))
    prof["chunking_strategy_name"] = ask("Chunking strategy:", default=prof.get("chunking_strategy_name"))
    logger.info("Profile %s updated", pid)
    return profiles

def delete_profile(profiles: Dict[str, Any]) -> Dict[str, Any]:
    pid = select_profile(profiles)
    if pid and yes_no(f"Really delete profile {pid}?"):
        profiles.pop(pid)
        logger.info("Profile %s removed", pid)
    return profiles

# --------------------------------------------------------------------------- #
#                            job management functions                         #
# --------------------------------------------------------------------------- #

def menu_jobs(jobs: List[Dict[str, Any]], profiles: Dict[str, Any]) -> List[Dict[str, Any]]:
    while True:
        choice = menu_choice("Processing jobs", ["Create", "Edit", "Delete", "Back"])
        if choice == "Create":
            jobs = create_job(jobs, profiles)
        elif choice == "Edit":
            jobs = edit_job(jobs, profiles)
        elif choice == "Delete":
            jobs = delete_job(jobs)
        else:
            return jobs

def select_job(jobs: List[Dict[str, Any]]) -> int | None:
    if not jobs:
        logger.warning("No jobs defined")
        return None
    titles = [f"{i}. {j['job_id']} ({j['author_name']})" for i, j in enumerate(jobs)]
    sel = menu_choice("Select job", titles + ["Cancel"])
    if sel == "Cancel":
        return None
    return int(sel.split(".")[0])

def create_job(jobs: List[Dict[str, Any]], profiles: Dict[str, Any]) -> List[Dict[str, Any]]:
    jid = ask("Job ID (snake‑case):", validate=r"^[a-z0-9_-]+$")
    if any(j["job_id"] == jid for j in jobs):
        logger.warning("Job %s already exists", jid)
        return jobs
    author = ask("Author name:")
    lang = ask("Language code (ISO‑639‑1):", default="es", validate=r"^[a-z]{2}$")
    origin = ask("Origin type (e.g. Telegram Archive):")
    source_dir = ask("Source directory inside raw_data/:")
    profile_name = menu_choice("Content profile", list(profiles.keys()))

    job: Dict[str, Any] = {
        "job_id": jid,
        "author_name": author,
        "language_code": lang,
        "origin_type_name": origin,
        "source_directory_name": source_dir,
        "content_profile_name": profile_name,
    }

    # extra parser rules for json_like
    if profiles[profile_name]["source_format_group"] == "json_like":
        rules = ask_filter_rules()
        if rules:
            if "parser_config" not in job:
                job["parser_config"] = {}
            job["parser_config"]["filter_rules"] = rules

    jobs.append(job)
    logger.info("Job %s created", jid)
    return jobs

def edit_job(jobs: List[Dict[str, Any]], profiles: Dict[str, Any]) -> List[Dict[str, Any]]:
    idx = select_job(jobs)
    if idx is None:
        return jobs
    
    job = jobs[idx]
    job["author_name"] = ask("Author name:", default=job.get("author_name"))
    job["language_code"] = ask("Language code:", default=job.get("language_code"), validate=r"^[a-z]{2}$")
    profile_name = menu_choice("Content profile", list(profiles.keys()), default=job.get("content_profile_name"))
    job["content_profile_name"] = profile_name
    
    # Update filter rules if json_like profile
    if profiles[profile_name]["source_format_group"] == "json_like":
        if "parser_config" in job and "filter_rules" in job["parser_config"]:
            print("Current filter rules:", job["parser_config"]["filter_rules"])
        
        if yes_no("Edit filter rules?"):
            rules = ask_filter_rules()
            if rules:
                if "parser_config" not in job:
                    job["parser_config"] = {}
                job["parser_config"]["filter_rules"] = rules
            elif "parser_config" in job:
                job["parser_config"].pop("filter_rules", None)
    
    logger.info("Job %s updated", job["job_id"])
    return jobs

def delete_job(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    idx = select_job(jobs)
    if idx is None:
        return jobs
    
    job_id = jobs[idx]["job_id"]
    if yes_no(f"Really delete job {job_id}?"):
        jobs.pop(idx)
        logger.info("Job %s deleted", job_id)
    return jobs

# --------------------------------------------------------------------------- #
#                                 Main entry point                            #
# --------------------------------------------------------------------------- #

def main():
    parser = argparse.ArgumentParser(description="Biblioperson ETL configuration CLI")
    parser.add_argument("--validate", action="store_true", help="Validate existing configurations")
    args = parser.parse_args()
    
    profiles = load_json(CONTENT_PROFILES_PATH, {})
    jobs = load_json(JOBS_CONFIG_PATH, [])
    
    if args.validate:
        # TODO: implement validation against schemas
        print("Validation not yet implemented")
        return
    
    while True:
        choice = menu_choice(
            "Biblioperson ETL Configuration",
            ["Content Profiles", "Processing Jobs", "Save and Exit"]
        )
        
        if choice == "Content Profiles":
            profiles = menu_profiles(profiles)
        elif choice == "Processing Jobs":
            jobs = menu_jobs(jobs, profiles)
        else:  # Save and Exit
            save_json(CONTENT_PROFILES_PATH, profiles)
            save_json(JOBS_CONFIG_PATH, jobs)
            logger.info("Configuration saved. Goodbye!")
            break

if __name__ == "__main__":
    main()
