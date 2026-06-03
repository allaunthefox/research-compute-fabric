#!/usr/bin/env python3
"""
Reservoir CLI — FTP-backed storage with local caching and receipt chain.
Works without network by operating on local cache, syncs to FTP reservoir.
"""

import argparse, base64, hashlib, json, os, shutil, sys, time
from pathlib import Path
from typing import Optional

try:
    import pycurl
    HAS_CURL = True
except ImportError:
    HAS_CURL = False


# ─── Q16_16 helpers ─────────────────────────────────────────────────────────

class Q16_16:
    @staticmethod
    def of_int(x: int) -> int:
        return x << 16

    @staticmethod
    def to_int(x: int) -> int:
        return x >> 16


# ─── Receipt ID ─────────────────────────────────────────────────────────────

def receipt_id() -> str:
    return hashlib.sha256(str(time.time_ns()).encode()).hexdigest()[:32]

def now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return "sha256:" + h.hexdigest()


# ─── FTP Operations (curl-based, no extra deps) ─────────────────────────────

class FTPClient:
    def __init__(self, host: str, user: str, password: str, base_path: str = "/htdocs"):
        self.host = host
        self.user = user
        self.password = password
        self.base_path = base_path.rstrip("/")
        self.curl = None
        if HAS_CURL:
            self.curl = pycurl.Curl()
            self.curl.setopt(pycurl.FTP_CREATE_MISSING_DIRS, 1)
            self.curl.setopt(pycurl.FTP_USE_EPSV, 0)

    def _url(self, path: str) -> str:
        p = (self.base_path + "/" + path.lstrip("/")).replace("//", "/")
        return f"ftp://{self.host}{p}"

    def list(self, path: str = "") -> list[str]:
        cmd = f"LIST{'-la' if True else ''}"
        out = []
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self._url(path))
        c.setopt(pycurl.USERNAME, self.user)
        c.setopt(pycurl.PASSWORD, self.password)
        c.setopt(pycurl.FTP_CREATE_MISSING_DIRS, 0)
        c.setopt(pycurl.NOBODY, 0)
        c.setopt(pycurl.VERBOSE, 0)
        import io
        buf = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        try:
            c.perform()
            raw = buf.getvalue().decode()
            for line in raw.split("\n"):
                if line.strip():
                    out.append(line)
        except Exception as e:
            pass
        c.close()
        return out

    def mkdir(self, path: str) -> bool:
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self._url(path))
        c.setopt(pycurl.USERNAME, self.user)
        c.setopt(pycurl.PASSWORD, self.password)
        c.setopt(pycurl.FTP_CREATE_MISSING_DIRS, 1)
        c.setopt(pycurl.CUSTOMREQUEST, "MKD " + path)
        try:
            c.perform()
            c.close()
            return True
        except Exception:
            return False

    def upload_file(self, local_path: Path, remote_path: str) -> bool:
        c = pycurl.Curl()
        c.setopt(pycurl.UPLOAD, 1)
        c.setopt(pycurl.URL, self._url(remote_path))
        c.setopt(pycurl.USERNAME, self.user)
        c.setopt(pycurl.PASSWORD, self.password)
        c.setopt(pycurl.FTP_CREATE_MISSING_DIRS, 1)
        f = open(local_path, "rb")
        c.setopt(pycurl.READDATA, f)
        try:
            c.perform()
            f.close()
            c.close()
            return True
        except Exception as e:
            f.close()
            c.close()
            return False

    def download_file(self, remote_path: str, local_path: Path) -> bool:
        import io
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self._url(remote_path))
        c.setopt(pycurl.USERNAME, self.user)
        c.setopt(pycurl.PASSWORD, self.password)
        buf = io.BytesIO()
        c.setopt(pycurl.WRITEFUNCTION, buf.write)
        try:
            c.perform()
            local_path.write_bytes(buf.getvalue())
            c.close()
            return True
        except Exception:
            c.close()
            return False

    def exists(self, path: str) -> bool:
        c = pycurl.Curl()
        c.setopt(pycurl.NOBODY, 1)
        c.setopt(pycurl.URL, self._url(path))
        c.setopt(pycurl.USERNAME, self.user)
        c.setopt(pycurl.PASSWORD, self.password)
        try:
            c.perform()
            code = c.getinfo(pycurl.HTTP_CODE)
            c.close()
            return code in (200, 226, 250)
        except Exception:
            c.close()
            return False

    def delete(self, path: str) -> bool:
        c = pycurl.Curl()
        c.setopt(pycurl.URL, self._url(path))
        c.setopt(pycurl.USERNAME, self.user)
        c.setopt(pycurl.PASSWORD, self.password)
        c.setopt(pycurl.CUSTOMREQUEST, "DELE " + path)
        try:
            c.perform()
            c.close()
            return True
        except Exception:
            c.close()
            return False


# ─── Local Reservoir ──────────────────────────────────────────────────────────

class LocalReservoir:
    """Filesystem-backed reservoir with manifest + receipts."""

    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        self.storage = self.root / "storage"
        self.uploads = self.storage / "uploads"
        self.receipts_dir = self.storage / "receipts"
        self.manifest_file = self.storage / "manifest.json"
        for d in [self.storage, self.uploads, self.receipts_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def _manifest(self) -> dict:
        if self.manifest_file.exists():
            return json.loads(self.manifest_file.read_text())
        return {}

    def _save_manifest(self, m: dict):
        self.manifest_file.write_text(json.dumps(m, indent=2))

    def health(self) -> dict:
        m = self._manifest()
        return {
            "status": "reservoir-up",
            "version": "1.0.0",
            "mode": "local",
            "timestamp": now_iso(),
            "root": str(self.root),
            "package_count": len(m),
        }

    def list_packages(self) -> dict:
        m = self._manifest()
        return {"packages": [{"pkg": k, **v} for k, v in m.items()], "total": len(m)}

    def get_package(self, pkg: str) -> dict:
        m = self._manifest()
        if pkg not in m:
            raise FileNotFoundError(f"Package '{pkg}' not found")
        return {"pkg": pkg, **m[pkg]}

    def register_bytes(self, pkg: str, data: bytes, promotion_state: str = "held",
                       source: str = "local") -> dict:
        content_hash = "sha256:" + hashlib.sha256(data).hexdigest()
        size = len(data)
        ch_short = content_hash[7:]

        # Write content file
        (self.uploads / (ch_short + ".bin")).write_bytes(data)

        # Update manifest
        m = self._manifest()
        now = now_iso()
        if pkg in m:
            old = m[pkg]["created_at"]
            m[pkg] = {
                "pkg": pkg,
                "content_hash": content_hash,
                "size_bytes": size,
                "promotion_state": promotion_state,
                "source": source,
                "created_at": old,
                "updated_at": now,
            }
        else:
            m[pkg] = {
                "pkg": pkg,
                "content_hash": content_hash,
                "size_bytes": size,
                "promotion_state": promotion_state,
                "source": source,
                "created_at": now,
                "updated_at": now,
            }
        self._save_manifest(m)

        # Write receipt
        rid = receipt_id()
        receipt = {
            "id": rid,
            "pkg": pkg,
            "receipt_type": "package_register",
            "content_hash": content_hash,
            "size_bytes": size,
            "promotion_state": promotion_state,
            "source": source,
            "created_at": now,
        }
        (self.receipts_dir / f"{rid}.json").write_text(json.dumps(receipt, indent=2))
        return {"status": "registered", "pkg": pkg, "content_hash": content_hash, "receipt_id": rid}

    def register_file(self, pkg: str, path: Path, promotion_state: str = "held") -> dict:
        return self.register_bytes(pkg, path.read_bytes(), promotion_state, source="local-file")

    def update_promotion(self, pkg: str, new_state: str) -> dict:
        m = self._manifest()
        if pkg not in m:
            raise FileNotFoundError(f"Package '{pkg}' not found")
        old_state = m[pkg].get("promotion_state", "held")
        now = now_iso()
        m[pkg]["promotion_state"] = new_state
        m[pkg]["updated_at"] = now
        self._save_manifest(m)

        rid = receipt_id()
        receipt = {
            "id": rid,
            "pkg": pkg,
            "receipt_type": "promotion_change",
            "from_state": old_state,
            "to_state": new_state,
            "created_at": now,
        }
        (self.receipts_dir / f"{rid}.json").write_text(json.dumps(receipt, indent=2))
        return {"status": "promotion_updated", "pkg": pkg, "from": old_state, "to": new_state}

    def list_receipts(self) -> list[dict]:
        receipts = []
        for f in sorted(self.receipts_dir.glob("*.json")):
            receipts.append(json.loads(f.read_text()))
        return receipts

    def download(self, pkg: str) -> bytes:
        m = self._manifest()
        if pkg not in m:
            raise FileNotFoundError(f"Package '{pkg}' not found")
        ch = m[pkg]["content_hash"]
        return (self.uploads / (ch[7:] + ".bin")).read_bytes()

    def delete(self, pkg: str) -> dict:
        m = self._manifest()
        if pkg not in m:
            raise FileNotFoundError(f"Package '{pkg}' not found")
        ch = m[pkg]["content_hash"]
        uf = self.uploads / (ch[7:] + ".bin")
        if uf.exists():
            uf.unlink()
        del m[pkg]
        self._save_manifest(m)
        return {"status": "deleted", "pkg": pkg}


# ─── FTP Sync ───────────────────────────────────────────────────────────────

class FTPSync:
    """Push/pull local reservoir ↔ FTP endpoint."""

    def __init__(self, ftp: FTPClient, local: LocalReservoir):
        self.ftp = ftp
        self.local = local

    def push_all(self) -> dict:
        """Push all local packages to FTP reservoir."""
        manifest = self.local._manifest()
        pushed = []
        errors = []

        # Ensure remote directories exist
        self.ftp.mkdir("storage/uploads")
        self.ftp.mkdir("storage/receipts")

        for pkg, info in manifest.items():
            ch = info["content_hash"]
            local_file = self.local.uploads / (ch[7:] + ".bin")
            if not local_file.exists():
                errors.append({"pkg": pkg, "error": "content file missing"})
                continue

            # Upload content
            ok = self.ftp.upload_file(local_file, f"storage/uploads/{ch[7:]}.bin")
            if not ok:
                errors.append({"pkg": pkg, "error": "upload failed"})
                continue

            # Upload receipt if exists
            receipts = self.local.list_receipts()
            pkg_receipts = [r for r in receipts if r["pkg"] == pkg]
            for r in pkg_receipts:
                rid = r["id"]
                local_receipt = self.local.receipts_dir / f"{rid}.json"
                if local_receipt.exists():
                    self.ftp.upload_file(local_receipt, f"storage/receipts/{rid}.json")

            pushed.append(pkg)

        # Upload manifest
        manifest_bytes = json.dumps(manifest, indent=2).encode()
        self.ftp.upload_file(
            self.local.manifest_file,
            "storage/manifest.json"
        )

        return {"pushed": pushed, "total": len(pushed), "errors": errors}

    def pull_all(self) -> dict:
        """Pull all packages from FTP reservoir to local."""
        if not self.ftp.exists("storage/manifest.json"):
            return {"pulled": [], "total": 0, "errors": ["no remote manifest"]}

        # Download manifest
        tmp_manifest = self.local.storage / "manifest.remote.json"
        if not self.ftp.download_file("storage/manifest.json", tmp_manifest):
            return {"pulled": [], "total": 0, "errors": ["failed to download manifest"]}

        remote_m = json.loads(tmp_manifest.read_text())
        local_m = self.local._manifest()
        local_pkgs = set(local_m.keys())
        remote_pkgs = set(remote_m.keys())

        pulled = []
        errors = []

        for pkg in remote_pkgs:
            if pkg in local_pkgs:
                # Skip existing unless content differs
                local_hash = local_m[pkg].get("content_hash")
                remote_hash = remote_m[pkg].get("content_hash")
                if local_hash == remote_hash:
                    continue

            ch = remote_m[pkg]["content_hash"]
            remote_content = f"storage/uploads/{ch[7:]}.bin"
            local_content = self.local.uploads / (ch[7:] + ".bin")

            if self.ftp.download_file(remote_content, local_content):
                # Update local manifest
                local_m[pkg] = remote_m[pkg]
                local_m[pkg]["created_at"] = remote_m[pkg].get("created_at", now_iso())
                local_m[pkg]["updated_at"] = now_iso()
                pulled.append(pkg)
            else:
                errors.append({"pkg": pkg, "error": "content download failed"})

        self.local._save_manifest(local_m)

        # Sync receipts
        if self.ftp.exists("storage/receipts"):
            for pkg in pulled:
                receipts = self.local.list_receipts()
                for r in receipts:
                    rid = r["id"]
                    local_receipt = self.local.receipts_dir / f"{rid}.json"
                    if not local_receipt.exists():
                        self.ftp.download_file(f"storage/receipts/{rid}.json", local_receipt)

        tmp_manifest.unlink()
        return {"pulled": pulled, "total": len(pulled), "errors": errors}

    def push_receipt(self, receipt: dict) -> bool:
        rid = receipt["id"]
        path = self.local.receipts_dir / f"{rid}.json"
        if path.exists():
            return self.ftp.upload_file(path, f"storage/receipts/{rid}.json")
        return False


# ─── CLI ────────────────────────────────────────────────────────────────────

def cmd_health(rv, args):
    print(json.dumps(rv.health(), indent=2))

def cmd_list(rv, args):
    result = rv.list_packages()
    print(json.dumps(result, indent=2))

def cmd_register(rv, args):
    path = Path(args.file)
    if not path.exists():
        print(f"ERROR: file not found: {path}", file=sys.stderr)
        return 1
    result = rv.register_file(args.pkg or path.stem, path, args.state)
    print(json.dumps(result, indent=2))
    return 0

def cmd_promote(rv, args):
    print(json.dumps(rv.update_promotion(args.pkg, args.state), indent=2))

def cmd_receipts(rv, args):
    print(json.dumps(rv.list_receipts(), indent=2))

def cmd_download(rv, args):
    data = rv.download(args.pkg)
    out = Path(args.output) if args.output else Path(args.pkg + ".bin")
    out.write_bytes(data)
    print(f"Downloaded → {out} ({len(data)} bytes)")

def cmd_delete(rv, args):
    print(json.dumps(rv.delete(args.pkg), indent=2))

def cmd_push(rv, args):
    ftp = FTPClient(args.ftp_host, args.ftp_user, args.ftp_pass)
    sync = FTPSync(ftp, rv)
    result = sync.push_all()
    print(json.dumps(result, indent=2))

def cmd_pull(rv, args):
    ftp = FTPClient(args.ftp_host, args.ftp_user, args.ftp_pass)
    sync = FTPSync(ftp, rv)
    result = sync.pull_all()
    print(json.dumps(result, indent=2))

def cmd_seed(rv, args):
    """Seed the reservoir with initial packages from a directory."""
    src = Path(args.src)
    if not src.exists():
        print(f"ERROR: source directory not found: {src}", file=sys.stderr)
        return 1

    seeded = []
    for f in src.rglob("*"):
        if f.is_file() and not f.name.startswith("."):
            pkg_name = str(f.relative_to(src)).replace("/", "__")
            try:
                result = rv.register_file(pkg_name, f, "held")
                seeded.append(pkg_name)
            except Exception as e:
                print(f"  SKIP {pkg_name}: {e}", file=sys.stderr)

    print(f"Seeded {len(seeded)} packages from {src}")
    return 0


def main():
    p = argparse.ArgumentParser(description="Reservoir CLI — FTP-backed research storage")
    sub = p.add_subparsers(dest="cmd", required=True)

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--root", default=os.environ.get("RESERVOIR_ROOT", "./reservoir-data"),
                        help="Local reservoir root")

    # health
    sub.add_parser("health", parents=[common], help="Health check")

    # list
    sub.add_parser("list", parents=[common], help="List packages")

    # register
    reg = sub.add_parser("register", parents=[common], help="Register a package")
    reg.add_argument("file", help="File to register")
    reg.add_argument("--pkg", help="Package name (default: filename)")
    reg.add_argument("--state", default="held", help="Promotion state")

    # promote
    pro = sub.add_parser("promote", parents=[common], help="Update promotion state")
    pro.add_argument("pkg", help="Package name")
    pro.add_argument("state", help="New state (held/semi/promoted)")

    # receipts
    sub.add_parser("receipts", parents=[common], help="List receipts")

    # download
    dl = sub.add_parser("download", parents=[common], help="Download package")
    dl.add_argument("pkg", help="Package name")
    dl.add_argument("--output", "-o", help="Output file")

    # delete
    del_p = sub.add_parser("delete", parents=[common], help="Delete package")
    del_p.add_argument("pkg", help="Package name")

    # push
    push = sub.add_parser("push", parents=[common], help="Push to FTP reservoir")
    push.add_argument("--ftp-host", default=os.environ.get("FTP_HOST", "ftpupload.net"),
                     help="FTP host")
    push.add_argument("--ftp-user", default=os.environ.get("FTP_USER", "if0_42058601"),
                     help="FTP user")
    push.add_argument("--ftp-pass", default=os.environ.get("FTP_PASS", ""),
                     help="FTP password")

    # pull
    pull = sub.add_parser("pull", parents=[common], help="Pull from FTP reservoir")
    pull.add_argument("--ftp-host", default=os.environ.get("FTP_HOST", "ftpupload.net"))
    pull.add_argument("--ftp-user", default=os.environ.get("FTP_USER", "if0_42058601"))
    pull.add_argument("--ftp-pass", default=os.environ.get("FTP_PASS", ""))

    # seed
    seed = sub.add_parser("seed", parents=[common], help="Seed from directory")
    seed.add_argument("src", help="Source directory")

    args = p.parse_args()
    rv = LocalReservoir(Path(args.root))

    cmds = {
        "health": cmd_health,
        "list": cmd_list,
        "register": cmd_register,
        "promote": cmd_promote,
        "receipts": cmd_receipts,
        "download": cmd_download,
        "delete": cmd_delete,
        "push": cmd_push,
        "pull": cmd_pull,
        "seed": cmd_seed,
    }
    cmds[args.cmd](rv, args)


if __name__ == "__main__":
    main()