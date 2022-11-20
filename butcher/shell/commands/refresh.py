import logging
from collections import defaultdict
from pathlib import Path

import click

from butcher.data import dump_json, load_json
from butcher.parsers.entities.entity_type import ENTITY_CATEGORY, detect_entity_type_by_name
from butcher.shell.config import ProjectConfig, pass_config

logger = logging.getLogger(__name__)


@click.command("refresh", help="Update entities from docs")
@pass_config
def command_refresh(config: ProjectConfig):
    click.echo("Refreshing entities tree...")

    docs = load_json(path=config.project_dir / "schema" / "schema.json")
    known_entities = defaultdict(set)

    skipped = 0
    added = 0
    updated = 0
    deprecated = 0

    for group in docs["items"]:
        for entity in group["children"]:
            entity_category = detect_entity_type_by_name(entity["name"])
            known_entities[entity_category].add(entity["name"])

            entity_dir: Path = (
                config.project_dir / ENTITY_CATEGORY[entity_category] / entity["name"]
            )
            entity_dir.mkdir(parents=True, exist_ok=True)
            entity_data_path = entity_dir / "entity.json"

            meta = {"deprecated": False}
            group_info = {
                "title": group["title"],
                "anchor": group["anchor"],
            }

            if entity_data_path.exists():
                logger.info("Refreshed entity in %s", entity_dir)
                entity_data = load_json(path=entity_data_path)
                entity_data["object"] = entity
                entity_data["group"] = group_info
                entity_data["meta"].update(meta)
                if dump_json(
                    value={
                        "meta": entity_data["meta"],
                        "group": entity_data["group"],
                        "object": entity_data["object"],
                    },
                    path=entity_data_path,
                ):
                    updated += 1
                else:
                    skipped += 1
            else:
                logger.info("Created entity in %s", entity_dir)
                dump_json(
                    value={
                        "meta": meta,
                        "group": group_info,
                        "object": entity,
                    },
                    path=entity_data_path,
                )
                added += 1

    for entity_type, entity_names in known_entities.items():
        entities_dir = config.project_dir / ENTITY_CATEGORY[entity_type]
        for entity_data_path in entities_dir.glob("**/entity.json"):
            if entity_data_path.parent.name not in entity_names:
                entity_data = load_json(path=entity_data_path)
                if entity_data["meta"].get("deprecated"):
                    continue
                deprecated += 1
                logger.warning("Entity marked as deprecated in %s", entity_data_path.parent)
                entity_data["meta"]["deprecated"] = True
                dump_json(path=entity_data_path, value=entity_data)

    if added:
        logger.info("Added new %d entities", added)
    if skipped:
        logger.info("Skipped %d entities", skipped)
    if updated:
        logger.info("Updated %d entities", updated)
    if deprecated:
        logger.info("Deprecated %d entities", deprecated)
