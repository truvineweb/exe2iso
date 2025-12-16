# exe2iso

**exe2iso** is a lightweight tool for converting Windows `.exe` installers into `.iso` images. Useful for extracting installation contents or repacking self-extracting executables into a mountable ISO format.

## Features

- Convert `.exe` installers to `.iso`
- Supports basic extraction of setup payloads
- CLI-friendly and scriptable
- Ideal for research, reverse engineering, or archival use

## Use cases

- Repackaging legacy installers for virtual machines
- Extracting files from SFX installers
- Creating bootable ISOs from setup files

## Usage

```bash
exe2iso input-installer.exe output-image.iso
