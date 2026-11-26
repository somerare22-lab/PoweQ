# PoweQ

**PoweQ** is an independent, configurable build utility focused on Minecraft Paper plugins and Data Packs. Python orchestrates builds and Java plugins are compiled with the JDK's `javac`. It is a lightweight Gradle-style alternative/prototype.

**Version:** 0.1.0 (prototype)

## Requirements
- Python 3.11+
- JDK with `java` and `javac`
- Paper API JAR for plugin builds
- No third-party Python packages

## Quick start: Paper plugin
```sh
python powerq.py init ExamplePlugin --type paper
cd ExamplePlugin
```
Edit `powerq.toml`, set the local Paper API JAR path:
```toml
[paper]
api = "1.21.11"
api_jar = "C:/path/to/paper-api.jar"
libraries = []
```
Build:
```sh
python ../powerq.py build
```
Artifact: `build/ExamplePlugin.jar`

## Data Pack
```sh
python powerq.py init ExamplePack --type datapack
cd ExamplePack
python ../powerq.py build
```
The ZIP archive is output in `build/`.

## Commands
| Command | Purpose |
|---|---|
| `init NAME --type paper` | Generate Paper plugin project |
| `init NAME --type datapack` | Generate Data Pack project |
| `build` | Build project from current folder |
| `clean` | Remove configured output directory |
| `doctor` | Print Python and Java tool versions |
| `--version` | Print PoweQ version |

## Configuration
- `compiler.java`: Java release for `javac --release`
- `paper.api_jar`: local Paper API JAR
- `paper.libraries`: local JARs added to compile classpath
- `build.output`: output folder
- `build.jar`: archive filename

## Project layout
Paper: `src/main/java` and `src/main/resources`. PoweQ generates `plugin.yml` during the build.
Data Pack: put pack files under `src/`; `pack.mcmeta` is required.

## Limitations
This early version does not resolve Maven dependencies, download Paper API automatically, bundle dependency JARs, or comprehensively validate Data Pack schemas. Data Pack format is currently initialized to a sample value and should be adjusted for the target Minecraft version.

## License
MIT.
