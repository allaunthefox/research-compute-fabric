# System Software Inventory — 2026-05-13

**Host:** CachyOS (Arch-based)  
**Total explicitly installed packages:** 391  
**Generated:** Post-FAMM codebase memory preservation commit `7bddd21a`

---

## VITAL — Do Not Remove

These are the backbone. Without them, the system does not boot, authenticate, update, or connect.

| Package | Why |
|---|---|
| `base` | Base system files. Removing this breaks everything. |
| `base-devel` | Build toolchain (gcc, make, etc.). Needed for AUR and from-source work. |
| `linux-cachyos` + `headers` | Custom CachyOS kernel with BORE scheduler. Boot-critical. |
| `linux-cachyos-lts` + `headers` | LTS fallback kernel. Boot-critical redundancy. |
| `linux-firmware` | Hardware firmware blobs. WiFi, GPU, NIC will fail without. |
| `amd-ucode` | AMD CPU microcode updates. Security + stability. |
| `nvidia-580xx-dkms` + `utils` + `settings` + `opencl` | GPU driver stack. Display + CUDA + ML workloads. |
| `lib32-nvidia-580xx-utils` + `lib32-vulkan-*` | 32-bit compatibility for GPU (Steam, Wine). |
| `mkinitcpio` | Initramfs generation. Boot-critical. |
| `efibootmgr` + `efitools` | EFI boot entry management. |
| `limine` + `limine-mkinitcpio-hook` + `limine-snapper-sync` | Your bootloader + snapper rollback integration. |
| `device-mapper` + `lvm2` + `cryptsetup` | Block device layer. LUKS + LVM. |
| `btrfs-progs` + `snapper` | Filesystem tools + snapshot management. |
| `networkmanager` + `iwd` | Network connectivity. |
| `openssh` | Remote access. |
| `sudo` | Privilege escalation. |
| `iptables` | Firewall backend. |
| `pacman` + `pacman-contrib` + `paru` + `yay` + `aurutils` | Package management. Without these you cannot install anything. |
| `systemd` (via `base`) | Init system. Implicit but critical. |
| `pipewire` + `wireplumber` + `alsa-*` | Audio stack. |
| `mesa` (via `base` / `plasma`) | OpenGL/Vulkan for AMD iGPU fallback. |
| `noto-fonts` + `noto-fonts-cjk` + `noto-fonts-emoji` | System font coverage. Broken UI without. |

---

## NEEDED — Core Workflow

You use these daily or weekly for the Research Stack, Nous Research, or your primary identity.

| Package | Why |
|---|---|
| `git` + `github-cli` | Source control. Non-negotiable for Research Stack. |
| `rustup` + `cargo` | Rust toolchain. `codebase-memory` crate + FAMM runtime. |
| `elan-lean` + `lean` + `lake` | Lean 4 theorem prover. Core formalism stack. |
| `python` + `pip` + `python-virtualenv` | Python runtime. Lean extraction scripts, ML pipelines. |
| `python-pytorch-opt-cuda` | ML framework. FAMM thermal models, Hermes inference. |
| `python-transformers` | HuggingFace transformers. LLM backend for Hermes. |
| `python-bitsandbytes` | 4-bit quantization. Run large models on 12GB VRAM. |
| `python-cupy` + `python-cuda` | CUDA Python bindings. GPU compute scripts. |
| `ollama-cuda` | Local LLM inference server. Hermes/OmniToken backend. |
| `open-webui` | Web interface for Ollama. Your chat layer. |
| `docker` + `docker-compose` | Containerization. Infra surfaces, build environments. |
| `node` + `npm` + `pnpm` | Node.js. `open-webui`, any JS-based tooling. |
| `code` (VS Code) | Primary IDE. |
| `vim` | Terminal editing. Git commits, quick fixes. |
| `firefox` | Primary browser. |
| `chromium` | Secondary browser / webapp container. |
| `zsh` + `cachyos-zsh-config` | Shell. Your configured environment. |
| `fish` | Alternative shell. You have it configured. |
| `plasma-desktop` + `kde-*` + `breeze-*` | KDE desktop environment. Your GUI. |
| `konsole` | Terminal emulator. |
| `dolphin` | File manager. |
| `rclone` | Cloud sync. Google Drive backups, FAMM receipts. |
| `texlive-*` (basic, latexextra, mathscience, bibtexextra, fontsextra, etc.) | LaTeX ecosystem. Paper writing, FAMM docs. |
| `pandoc-cli` | Document conversion. Markdown ↔ PDF/DOCX. |
| `zotero-bin` | Reference management. Academic papers. |
| `obsidian` | Knowledge base / second brain. |
| `signal-desktop` | Secure comms. |
| `telegram-desktop` | Community / Nous Research channels. |
| `thunderbird` | Email client. |
| `bitwarden` | Password manager. |
| `tailscale` | Mesh VPN. Racknerd node access. |
| `nix` (not listed, but check) | If you use Nix, it's NEEDED. If not, ignore. |
| `wget` + `curl` (via `base`) | HTTP downloads. |
| `rsync` | File sync. Backups, deployment. |
| `bind` + `dnsmasq` | DNS tools. Network debugging. |
| `man-db` + `man-pages` + `texinfo` | Documentation. |
| `htop` / `btop` | System monitoring. |
| `glances` | Advanced system monitor. |
| `fastfetch` | System info display. |
| `smartmontools` | Disk health monitoring. |
| `fwupd` | Firmware updates. |

---

## USEFUL — Quality of Life

These improve productivity but have alternatives or are not daily-use.

| Package | Why | Alternative If Removed |
|---|---|---|
| `alacritty` | GPU terminal emulator. | `konsole` (already installed) |
| `btop` | Fancy `top`. | `htop` / `top` |
| `duf` | Disk usage viewer. | `df -h` |
| `ripgrep` | Fast grep. | `grep -r` |
| `fd` (not listed, check) | Fast find. | `find` |
| `fzf` (not listed, check) | Fuzzy finder. | Manual navigation |
| `meld` | Diff viewer. | `vimdiff` / `code --diff` |
| `kate` | KDE text editor. | `code` / `vim` |
| `okular` | PDF viewer. | Browser / `evince` |
| `gwenview` | Image viewer. | Browser |
| `spectacle` | Screenshot tool. | `scrcpy`? No — `grim` / manual |
| `kdeconnect` | Phone integration. | None |
| `libreoffice-fresh` | Office suite. | Google Docs / OnlyOffice |
| `okular` | PDF annotation. | `evince` |
| `zathura` (not listed) | Minimal PDF viewer. | — |
| `okular` | Already listed. | — |
| `blender` | 3D modeling. | Web-based? No good alternative. |
| `freecad` | CAD. | Your CAD harness? `text-to-cad`? |
| `openscad` | Script CAD. | Blender |
| `kicad` | PCB design. | Altium (paid) / web EDA |
| `freerouting` | PCB auto-router. | Manual routing in KiCad |
| `gowin-eda-*` | FPGA IDE. | Vivado (Xilinx) / open source |
| `yosys` | Open synthesis. | Commercial tools |
| `prjtrellis` | ECP5 FPGA tools. | — |
| `vtr` | Verilog-to-Routing. | — |
| `openfpgaloader` | FPGA programmer. | Vendor tools |
| `gtkwave` | Waveform viewer. | — |
| `inspectrum` | Signal analysis. | GNU Radio |
| `gqrx` | SDR receiver. | — |
| `gnuradio` | Signal processing. | Python + `scipy` |
| `julia` | Scientific computing. | Python + NumPy |
| `octave` | MATLAB alternative. | Python + SciPy |
| `sagemath` | Computer algebra. | Mathematica (paid) / SymPy |
| `gnuplot` | Plotting. | Python + matplotlib |
| `r` (not listed) | Statistics. | Python + pandas |
| `jupyter` / `wljs-notebook-bin` | Notebooks. | Plain Python scripts |
| `pandoc-cli` | Already NEEDED. | — |
| `z3` + `yices` + `cvc5-bin` | SMT solvers. | Manual proof / other solvers |
| `agda` + `agda-stdlib` | Dependent types. | Lean (already installed) |
| `rocq` / `isabelle` | Proof assistants. | Lean (already installed) |
| `wolframalpha` / `wolframclient` | CAS queries. | SageMath / SymPy |
| `bitcoin-git` | Bitcoin node. | Electrum (light) |
| `go-ethereum` | Ethereum node. | Infura / Alchemy API |
| `i2pd` | I2P router. | Tor (not listed) |
| `protonmail-bridge-bin` | Email encryption. | Webmail |
| `nheko-git` | Matrix client. | Element web |
| `obs-studio` (not listed) | Streaming. | — |
| `haruna` | Video player. | `vlc` (not listed) / browser |
| `vlc-plugins-all` | Media player backend. | `mpv` (not listed) |
| `strawberry` | Music player. | Browser / `ncspot` |
| `sox` | Audio processing. | `ffmpeg` |
| `tesseract` + `tesseract-data-eng` | OCR. | Online OCR |
| `unoconv` | Office doc conversion. | `pandoc` / `libreoffice --headless` |
| `pdf2htmlex` | PDF to HTML. | `pdftotext` |
| `scrcpy` | Android screen mirror. | None |
| `guiscrcpy-appimage` | GUI for scrcpy. | `scrcpy` CLI |
| `remmina` | Remote desktop. | `rdesktop` / `freerdp` |
| `sshfs` | SSH filesystem mount. | `rsync` / `sftp` |
| `nfs-utils` | NFS client/server. | `sshfs` / `rsync` |
| `qemu-*` | Virtualization. | `virtualbox` / `vmware` |
| `docker` | Already NEEDED. | — |
| `minikube` (not listed) | K8s local. | `kind` / raw Docker |
| `kubectl` (not listed) | K8s control. | — |
| `helm` (not listed) | K8s package manager. | — |
| `tabby` | Self-hosted AI coding assistant. | `code` + Copilot / local LLM |
| `cursor-bin` | AI-first IDE. | `code` + extensions |
| `windsurf-next` | AI IDE (Codeium). | `code` + extensions |
| `openai-codex-bin` | OpenAI coding agent. | Local LLM + continue.dev |
| `qwen-code-bin` | Alibaba coding model. | Local LLM |
| `claude-code-stable` | Anthropic CLI coding agent. | Local LLM |
| `gemini-cli-git` + `gemini-desktop-git` | Google AI tools. | Local LLM / web |
| `aichat-ng-bin` | Local chat CLI. | `ollama` + terminal |
| `chatblade` | ChatGPT CLI. | `aichat` / `tgpt` |
| `tgpt` | Terminal GPT. | `aichat` / `chatblade` |
| `opencode-bin` | Your coding agent? (meta!) | — |
| `linear-desktop-git` + `linear-native-tauri` | Project management. | Web app |
| `notion-app-enhanced` + `notion-native-tauri` | Notes / docs. | Web app / `obsidian` |
| `substack-local-preview` | Newsletter preview. | Web |
| `zotero-bin` | Already NEEDED. | — |
| `avogadro-*` | Molecular visualization. | Web-based ChemDoodle |
| `openbabel` | Chemistry file conversion. | Online converters |
| `samtools` + `bcftools` + `minimap2` | Bioinformatics. | Bioconda environment |
| `paraview` | Scientific visualization. | `visit` / Python + matplotlib |
| `etcher-bin` | USB image writer. | `dd` / `cp` |
| `etcher-bin` | Already listed. | — |
| `f3` | Flash drive tester. | `badblocks` |
| `hdparm` | Disk tuning. | `fio` |
| `dmidecode` | Hardware info. | `lshw` |
| `hwinfo` | Hardware probe. | `lspci` / `lsusb` |
| `hwdetect` | Hardware detection. | Manual |
| `lsscsi` | SCSI info. | `lsscsi` (unique) |
| `mdadm` | RAID management. | `btrfs` RAID |
| `jfsutils` + `xfsprogs` + `f2fs-tools` + `exfatprogs` | Alternative filesystems. | `btrfs` only |
| `nilfs-utils` | Log-structured FS. | `btrfs` snapshots |
| `os-prober` | Detect other OSes. | Manual `grub.cfg` edit |
| `upower` | Battery/power info. | `acpi` |
| `powerdevil` + `power-profiles-daemon` | Power management. | `tlp` |
| `cpupower` | CPU frequency control. | `auto-cpufreq` |
| `plymouth` + `plymouth-kcm` | Boot splash. | Text boot |
| `btrfs-assistant` | BTRFS GUI. | `btrfs` CLI |
| `filelight` | Disk usage GUI. | `du -sh` / `ncdu` |
| `ark` | Archive manager. | `tar` / `unzip` CLI |
| `partitionmanager` | Disk partitioning GUI. | `fdisk` / `gdisk` |
| `catfish` | File search GUI. | `find` / `ripgrep` |
| `kcalc` | Calculator. | `python` / `bc` |
| `kscreen` | Display management. | `xrandr` / `wlr-randr` |
| `kinfocenter` | System info GUI. | `fastfetch` / `neofetch` |
| `kwalletmanager` + `kwallet-pam` | Password storage. | `bitwarden` |
| `kio-admin` | Root file operations in Dolphin. | `sudo` + CLI |
| `plasma-*` (browser-integration, firewall, login-manager, nm, pa, systemmonitor, thunderbolt) | KDE addons. | Some optional |
| `kdeplasma-addons` | Extra widgets. | Remove if unused |
| `kdegraphics-thumbnailers` | Image thumbnails. | Fine to keep |
| `ffmpegthumbnailer` + `ffmpegthumbs` | Video thumbnails. | Fine to keep |
| `cachyos-*` (hello, packageinstaller, rate-mirrors, kernel-manager, settings, themes, wallpapers, hooks) | CachyOS customizations. | Theme/wallpaper optional |
| `cachyos-emerald-kde-theme-git` + `cachyos-nord-kde-theme-git` + `cachyos-iridescent-kde` | Themes. | Keep one, remove others |
| `cachyos-themes-sddm` | Login theme. | Optional |
| `cachyos-plymouth-bootanimation` | Boot animation. | Optional |
| `cachyos-wallpapers` | Wallpapers. | Optional |
| `awesome-terminal-fonts` + `char-white` + `ttf-*` | Fonts. | Keep minimal set |
| `ttf-meslo-nerd` | Nerd font for terminal. | Essential for icons |
| `cantarell-fonts` | GTK font. | Usually required |
| `ttf-bitstream-vera` + `ttf-dejavu` + `ttf-liberation` | Core fonts. | Keep |
| `ttf-opensans` | Common font. | Optional |
| `rebuild-detector` | AUR rebuild notifier. | Manual rebuild |
| `reflector` | Mirror ranking. | Static mirrorlist |
| `pkgfile` | File-to-package search. | `pacman -F` |
| `plocate` / `mlocate` | File database. | `find` |
| `pacman-contrib` | Extra pacman tools. | `checkupdates`, `paccache` useful |
| `logrotate` | Log management. | Manual cleanup |
| `usbutils` + `usb_modeswitch` | USB tools. | Debugging only |
| `ethtool` | NIC tuning. | Rarely needed |
| `modemmanager` | Cellular modems. | Remove if no modem |
| `bluez` + `bluedevil` + `bluez-*` | Bluetooth. | Remove if no BT devices |
| `networkmanager-openvpn` | VPN plugin. | `openvpn` CLI |
| `nss-mdns` | mDNS resolution. | `avahi` |
| `mariadb-libs` | MariaDB client libs. | Remove if no DB work |
| `nano` + `nano-syntax-highlighting` | Simple editor. | `vim` |
| `micro` | Modern terminal editor. | `vim` / `nano` |
| `less` | Pager. | `bat` (not listed) / `more` |
| `lbzip2` + `pbzip2` + `pigz` + `pixz` + `lrzip` + `lzop` + `lzip` + `zopfli` | Compression variants. | `gzip` + `xz` (base) |
| `aria2` | Multi-threaded downloader. | `wget` / `curl` |
| `unzip` + `unrar` | Archive extraction. | `p7zip` (not listed) |
| `pv` | Progress viewer. | `cat` |
| `s-nail` | Mail client. | `thunderbird` |
| `inetutils` | Telnet/ftp/hostname. | Rarely needed |
| `diffutils` | File diff. | `git diff` / `diff` (base) |
| `which` | Locate commands. | `command -v` |
| `glib2-devel` | GTK development. | Build dependency |
| `libvncserver` + `gtk-vnc` | VNC server/client. | `remmina` / `tigervnc` |
| `libva-nvidia-driver` | NVIDIA VA-API. | Video decode acceleration |
| `libxnvctrl-580xx` | NVIDIA control X extension. | `nvidia-settings` |
| `egl-wayland` | EGL on Wayland. | Wayland compatibility |
| `phonon-qt6-vlc` | KDE media backend. | Required for audio |
| `vlc-plugins-all` | VLC codecs. | `haruna` / `mpv` |
| `gst-*` | GStreamer plugins. | Required for KDE media |
| `opus-tools` | Opus codec CLI. | `ffmpeg` |
| `opus-tools` | Already listed. | — |

---

## IF YOU MUST — Consider Removing

These are heavy, redundant, or single-use. Reinstall on demand.

| Package | Size Impact | Why Remove | Reinstall When... |
|---|---|---|---|
| `libreoffice-fresh` + extensions | ~400MB | Heavy office suite. Use web or `onlyoffice-bin`. | You need offline doc editing. |
| `sagemath` | ~1GB | Huge CAS. Lean + Python/SymPy cover most. | Symbolic computation beyond SymPy. |
| `gnuradio` + `gqrx` + `inspectrum` | ~500MB | SDR stack. Single-purpose. | You buy an SDR dongle. |
| `julia` | ~400MB | Language overlap with Python. | You need Julia-specific packages. |
| `octave` | ~200MB | MATLAB clone. Python covers this. | You need `.m` file compatibility. |
| `paraview` | ~300MB | Scientific viz. Blender/Python can substitute. | You need parallel VTK rendering. |
| `avogadro-*` + `openbabel` | ~150MB | Chemistry niche. | You do molecular modeling. |
| `samtools` + `bcftools` + `minimap2` | ~100MB | Bioinformatics. | You sequence DNA. |
| `bitcoin-git` | ~200MB | Full node. Use lightweight wallet. | You need full validation. |
| `go-ethereum` | ~200MB | Full ETH node. Use remote RPC. | You need local validation. |
| `isabelle` | ~300MB | Proof assistant. You have Lean. | Isabelle-specific project. |
| `rocq` (Coq) | ~200MB | Proof assistant. You have Lean. | Coq-specific project. |
| `agda` + `stdlib` | ~150MB | Proof assistant. You have Lean. | Agda-specific project. |
| `freecad` | ~300MB | CAD overlap with `openscad` + `text-to-cad`. | Complex parametric modeling. |
| `blender` | ~500MB | Heavy. Keep if you use it. | 3D work. |
| `kicad` + `freerouting` | ~400MB | PCB design. | You design a board. |
| `gowin-eda-*` | ~200MB | FPGA IDE. Vendor-locked. | Gowin FPGA project. |
| `yosys` + `prjtrellis` + `vtr` + `openfpgaloader` | ~200MB | Open FPGA stack. | You synthesize for ECP5/iCE40. |
| `qemu-*` (all variants) | ~300MB | VMs. Docker covers most needs. | You need Windows VM or cross-arch. |
| `docker` | Already NEEDED. | — | — |
| `etcher-bin` | ~100MB | USB writer. `dd` works fine. | You need GUI for image writing. |
| `notion-*` (x2) | ~200MB | Electron wrappers for webapp. | Use browser. |
| `linear-*` (x2) | ~200MB | Electron wrappers for webapp. | Use browser. |
| `gemini-desktop-git` | ~150MB | Electron wrapper. | Use browser/CLI. |
| `cursor-bin` + `windsurf-next` + `openai-codex-bin` + `qwen-code-bin` + `claude-code-stable` | ~1GB total | AI IDEs/agents. You have `code` + local LLM. | You need that specific agent. |
| `tabby` | ~200MB | Self-hosted AI. Ollama covers this. | You want self-hosted Copilot. |
| `opencode-bin` | ~100MB | Meta — you're using it now! | Irony noted. |
| `chatblade` + `tgpt` + `aichat-ng-bin` | ~50MB each | Redundant CLI chat tools. | You prefer one over `aichat`. |
| `cachyos-wallpapers` + `cachyos-plymouth-bootanimation` + extra themes | ~50MB | Cosmetics. | You want the look. |
| `plymouth` (if you want text boot) | ~20MB | Boot splash. | You want quiet boot. |
| `nano` + `micro` | ~5MB | `vim` covers all editing. | You want beginner-friendly editor. |
| `jfsutils` + `xfsprogs` + `f2fs-tools` + `nilfs-utils` + `exfatprogs` | ~10MB each | FS tools you don't use. | You mount that filesystem. |
| `modemmanager` | ~10MB | No modem? | You get a 4G/5G dongle. |
| `bluez-*` (if no BT) | ~20MB | No Bluetooth devices? | You buy BT headphones/mouse. |
| `rebuild-detector` | ~1MB | AUR helper. Manual works. | You have many AUR packages. |
| `usb_modeswitch` | ~2MB | Modem/3G sticks. | You use a USB modem. |
| `inetutils` | ~5MB | Legacy tools. | You need `telnet`/`ftp`. |
| `s-nail` | ~2MB | Mail CLI. | You script email sending. |
| `protonmail-bridge-bin` | ~50MB | Bridge to Thunderbird. | You use PM + Thunderbird. |
| `scrcpy` + `guiscrcpy-appimage` | ~20MB | Android mirror. | You debug Android apps. |
| `remmina` | ~30MB | RDP/VNC client. | You remote to Windows. |
| `sshfs` | ~5MB | SSH mounts. | You use remote FS often. |
| `nfs-utils` | ~10MB | NFS. | You mount NFS shares. |
| `i2pd` | ~20MB | I2P router. | You need I2P anonymity. |
| `z3` + `yices` + `cvc5-bin` | ~50MB each | SMT solvers. | Formal methods project needs them. |
| `wolframalpha` + `wolframclient` | ~100MB | CAS queries. | You have Wolfram license. |
| `tungsten` | ? | Unknown. Check what it is. | — |
| `antigravity` | ? | Python easter egg? | — |
| `harper` | ? | Unknown. Check. | — |
| `tesseract` + data | ~30MB | OCR. | You scan documents. |
| `unoconv` | ~5MB | Doc conversion. | `pandoc` + `libreoffice` cover it. |
| `pdf2htmlex` | ~10MB | PDF→HTML. | You need that specific conversion. |
| `vlc-plugins-all` | ~50MB | All VLC codecs. | You play obscure formats. |
| `strawberry` | ~50MB | Music player. | You manage local music library. |
| `haruna` | ~20MB | Video player. | You want Qt video player. |
| `sox` | ~10MB | Audio processing CLI. | You script audio transforms. |
| `substack-local-preview` | ~20MB | Newsletter preview. | You write on Substack. |
| `wljs-notebook-bin` | ~100MB | Wolfram notebook. | You use Wolfram Language. |
| `xtensa-elf-binutils` | ~50MB | ESP32 toolchain. | You program ESP32. |
| `zig` | ~100MB | Language. | You have a Zig project. |
| `go` (not listed, check) | ~100MB | Language. | You have a Go project. |
| `java` / `jdk` (not listed) | ~200MB | JVM. | You run Java apps. |
| `scala` / `kotlin` (not listed) | ? | JVM languages. | — |

---

## Quick Wins — Remove These First

Estimated savings: **2-3GB** with zero functional loss.

```bash
# Redundant AI IDEs (keep one if you use it, or none)
sudo pacman -R cursor-bin windsurf-next openai-codex-bin qwen-code-bin claude-code-stable

# Redundant webapp wrappers (use browser instead)
sudo pacman -R notion-app-enhanced notion-native-tauri linear-desktop-git linear-native-tauri gemini-desktop-git

# Redundant chat CLIs (pick one favorite)
sudo pacman -R chatblade tgpt

# Heavy CAS overlap (keep Sage OR Julia OR Octave, not all)
sudo pacman -R sagemath julia octave

# SDR stack (if no dongle)
sudo pacman -R gnuradio gqrx inspectrum

# Office suite (if you use web/docs)
sudo pacman -R libreoffice-fresh libreoffice-extension-texmaths libreoffice-extension-writer2latex

# Full crypto nodes (use light wallets)
sudo pacman -R bitcoin-git go-ethereum

# Extra proof assistants (you have Lean)
sudo pacman -R isabelle rocq agda agda-stdlib

# Bioinformatics (if not sequencing)
sudo pacman -R samtools bcftools minimap2

# Chemistry (if not modeling)
sudo pacman -R avogadro-crystals avogadro-fragments avogadro-molecules avogadrolibs avogadrolibs-qt openbabel

# QEMU variants (keep only what you use)
sudo pacman -R qemu-system-x86 qemu-system-xtensa qemu-user-static qemu-user-static-binfmt

# Extra editors (vim covers all)
sudo pacman -R nano nano-syntax-highlighting micro

# Modem/bluetooth (if unused)
sudo pacman -R modemmanager bluez-hid2hci bluez-obex  # keep `bluez` + `bluedevil` if you use BT

# Extra filesystem tools (btrfs covers you)
sudo pacman -R jfsutils xfsprogs f2fs-tools nilfs-utils exfatprogs

# Plymouth (text boot is fine)
sudo pacman -R plymouth plymouth-kcm cachyos-plymouth-bootanimation

# Etcher (dd is enough)
sudo pacman -R etcher-bin
```

---

## Unchecked / Unknown

These weren't in the package list or I couldn't identify them. Verify manually:

- `go` (Golang) — check with `which go`
- `java` / `jdk` / `jre` — check with `java -version`
- `scala` / `kotlin` / `clojure` — JVM languages
- `haskell` / `ghc` / `stack` — check with `ghc --version`
- `dart` / `flutter` — check with `flutter --version`
- `elixir` / `erlang` — check with `elixir --version`
- `ruby` / `gem` — check with `ruby --version`
- `perl` (listed but minimal) — usually system dependency
- `php` — check with `php --version`
- `lua` — check with `lua -v`
- `R` — check with `R --version`
- `nix` — check with `nix --version`
- `guix` — check with `guix --version`
- `flatpak` — check with `flatpak --version`
- `appimageLauncher` / `appimaged` — AppImage integration
- `snapd` — check with `snap --version`
- `tlp` / `auto-cpufreq` — power management alternatives
- `fprintd` — fingerprint reader
- `touchegg` / `fusuma` — touchpad gestures
- `syncthing` — file sync alternative to rclone
- `nextcloud-client` / `dropbox` — cloud sync
- `steam` / `lutris` / `wine` — gaming
- `mpv` — video player alternative
- `bat` — `cat` with syntax highlighting
- `fd` — `find` alternative
- `fzf` — fuzzy finder
- `zoxide` — `cd` alternative
- `starship` — shell prompt
- `eza` / `exa` — `ls` alternative
- `direnv` — environment manager
- `nvm` / `fnm` — Node version managers
- `pyenv` / `uv` — Python version managers (you have `uv`-managed Python!)
- `poetry` / `pdm` / `hatch` — Python packaging
- `conda` / `mamba` — Scientific Python environment
- `asdf` — Universal version manager
- `ghcup` — Haskell toolchain manager
- `sdkman` — JVM toolchain manager
- `conda` / `mamba` — Data science environment
- `jupyterlab` / `notebook` — Web-based notebooks
- `neovim` / `nvim` — check with `nvim --version`
- `emacs` — check with `emacs --version`
- `idea` / `clion` / `pycharm` — JetBrains IDEs
- `android-studio` — Android dev
- `unityhub` / `godot` — Game engines
- `unreal-engine` — (unlikely, but check)

---

## Python Environment Note

You have **no user pip packages** (`pip list --user` returned empty). This is good — it means Python tools are either:
1. System packages (`python-*` from pacman)
2. Managed by `uv` (`.local/share/uv/python/...`)
3. In virtual environments (not shown)

If you use `uv` or `conda`, those environments are separate and not counted here.

---

## Rust/Cargo Note

Cargo-installed binaries:
- `aichat` v0.30.0 — CLI chat tool (redundant with `aichat-ng-bin` pacman package?)
- `wasm-pack` v0.14.0 — WebAssembly build tool

Keep `wasm-pack` if you do Rust→WASM. `aichat` may duplicate system package.

---

## Summary by Category

| Category | Count | Approx Size |
|---|---|---|
| **VITAL** | ~40 | ~2GB (kernel, drivers, base) |
| **NEEDED** | ~50 | ~3GB (toolchains, DE, browsers, comms) |
| **USEFUL** | ~150 | ~4GB (apps, devtools, media) |
| **IF YOU MUST** | ~150 | ~3GB (heavy/duplicate/niche) |
| **Total** | **391** | **~12-15GB** |

**Potential savings from aggressive cleanup:** 3-5GB by removing duplicates and heavy niche tools.

---

*Generated by OpenCode after preservation commit `7bddd21a`.*
