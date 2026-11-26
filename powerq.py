import argparse
import json
import shutil
import subprocess
import sys
import tomllib
import zipfile
from pathlib import Path

VERSION = "0.1.0"


def read_config(root):
    path = root / "powerq.toml"
    if not path.is_file():
        raise SystemExit("powerq.toml not found. Run 'powerq init' first.")
    with path.open("rb") as stream:
        return tomllib.load(stream)


def init_project(name, kind):
    root = Path(name)
    if root.exists() and any(root.iterdir()):
        raise SystemExit(f"Directory already exists and is not empty: {root}")
    root.mkdir(parents=True, exist_ok=True)
    package = name.lower().replace("-", "_")
    main_class = name
    main = f"net.example.{package}.{main_class}"
    config = f'''[project]
name = "{name}"
version = "1.0.0"
type = "{kind}"

[compiler]
java = 21

[paper]
api = "1.21.11"
api_jar = ""
libraries = []

[build]
output = "build"
jar = "{name}.jar"

[plugin]
main = "{main}"
author = "Developer"
description = "Built with PoweQ"
'''
    (root / "powerq.toml").write_text(config, encoding="utf-8")
    if kind == "paper":
        java_dir = root / "src/main/java" / Path("net/example") / package
        resources = root / "src/main/resources"
        java_dir.mkdir(parents=True)
        resources.mkdir(parents=True)
        (java_dir / f"{main_class}.java").write_text(f'''package net.example.{package};

import org.bukkit.plugin.java.JavaPlugin;

public final class {main_class} extends JavaPlugin {{
    @Override
    public void onEnable() {{
        getLogger().info("{name} enabled!");
    }}

    @Override
    public void onDisable() {{
        getLogger().info("{name} disabled!");
    }}
}}
''', encoding="utf-8")
    else:
        source = root / "src"
        (source / "data").mkdir(parents=True)
        (source / "pack.mcmeta").write_text(json.dumps(
            {"pack": {"pack_format": 48, "description": name}}, indent=2
        ), encoding="utf-8")
        function_dir = source / "data" / package / "function"
        function_dir.mkdir(parents=True)
        (function_dir / "hello.mcfunction").write_text(
            "say Hello from PoweQ!\n", encoding="utf-8"
        )
    print(f"Project created: {root}")


def run(command):
    result = subprocess.run(command)
    if result.returncode:
        raise SystemExit(result.returncode)


def build_paper(root, cfg):
    project, compiler, paper, build, plugin = (
        cfg["project"], cfg["compiler"], cfg["paper"], cfg["build"], cfg["plugin"]
    )
    sources = list((root / "src/main/java").rglob("*.java"))
    if not sources:
        raise SystemExit("No Java files found under src/main/java")
    api_file = paper.get("api_jar", "").strip()
    if not api_file:
        raise SystemExit("Configure paper.api_jar in powerq.toml")
    api = Path(api_file).expanduser()
    if not api.is_file():
        raise SystemExit(f"Paper API JAR not found: {api}")
    libraries = [Path(item).expanduser() for item in paper.get("libraries", [])]
    for library in libraries:
        if not library.is_file():
            raise SystemExit(f"Library JAR not found: {library}")
    classpath = [str(api.resolve()), *(str(p.resolve()) for p in libraries)]
    out = root / build["output"]
    classes = out / "classes"
    if classes.exists():
        shutil.rmtree(classes)
    classes.mkdir(parents=True)
    separator = ";" if sys.platform == "win32" else ":"
    command = [
        "javac", "-encoding", "UTF-8", "--release", str(compiler["java"]),
        "-cp", separator.join(classpath), "-d", str(classes.resolve()),
        *(str(source) for source in sources)
    ]
    print("PoweQ: compiling Java...")
    run(command)
    plugin_yml = (
        f"name: {project['name']}\n"
        f"version: {project['version']}\n"
        f"main: {plugin['main']}\n"
        f"api-version: \"{paper['api']}\"\n"
        f"author: {plugin['author']}\n"
        f"description: {plugin['description']}\n"
    )
    (classes / "plugin.yml").write_text(plugin_yml, encoding="utf-8")
    resources = root / "src/main/resources"
    if resources.exists():
        for item in resources.rglob("*"):
            if item.is_file():
                target = classes / item.relative_to(resources)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)
    jar_path = out / build["jar"]
    with zipfile.ZipFile(jar_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in classes.rglob("*"):
            if item.is_file():
                archive.write(item, item.relative_to(classes).as_posix())
    print(f"BUILD SUCCESS: {jar_path}")


def build_datapack(root, cfg):
    build = cfg["build"]
    source = root / "src"
    if not (source / "pack.mcmeta").is_file():
        raise SystemExit("Missing src/pack.mcmeta")
    output = root / build["output"]
    output.mkdir(parents=True, exist_ok=True)
    target = output / build["jar"]
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in source.rglob("*"):
            if item.is_file():
                archive.write(item, item.relative_to(source).as_posix())
    print(f"DATAPACK SUCCESS: {target}")


def build(root):
    cfg = read_config(root)
    kind = cfg["project"]["type"]
    if kind == "paper":
        build_paper(root, cfg)
    elif kind == "datapack":
        build_datapack(root, cfg)
    else:
        raise SystemExit(f"Unknown project type: {kind}")


def clean(root):
    cfg = read_config(root)
    output = root / cfg["build"]["output"]
    if output.exists():
        shutil.rmtree(output)
    print("Build output removed.")


def doctor():
    print(f"PoweQ {VERSION}")
    print(f"Python {sys.version.split()[0]}")
    for tool in ("java", "javac"):
        try:
            result = subprocess.run([tool, "-version"], capture_output=True, text=True)
            print(f"{tool}: {(result.stderr or result.stdout).strip()}")
        except FileNotFoundError:
            print(f"{tool}: not found")


def main():
    parser = argparse.ArgumentParser(prog="powerq", description="Minecraft Paper and Data Pack build utility")
    parser.add_argument("--version", action="version", version=f"PoweQ {VERSION}")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("init", help="Create a project")
    create.add_argument("name")
    create.add_argument("--type", choices=("paper", "datapack"), default="paper")
    commands.add_parser("build", help="Build current project")
    commands.add_parser("clean", help="Delete build directory")
    commands.add_parser("doctor", help="Check Java and Python")
    args = parser.parse_args()
    if args.command == "init":
        init_project(args.name, args.type)
    elif args.command == "build":
        build(Path.cwd())
    elif args.command == "clean":
        clean(Path.cwd())
    elif args.command == "doctor":
        doctor()


if __name__ == "__main__":
    main()
