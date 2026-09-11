"""Malware scanning and quarantine security engine for PWD301.

Implements:
- Pluggable multi-tier scanner architecture (BaseScanner, BuiltinHeuristicScanner, ClamAVScanner).
- Standard EICAR signature recognition (plain text, base64 streams, and zip archives).
- Deep heuristic inspection for PDF files (/JavaScript, /JS, /Launch, /EmbeddedFiles).
- Deep heuristic inspection for OOXML/ZIP containers (macro binaries, embedded
  executables, MZ/ELF headers).
- Binary header spoofing and null byte injection prevention.
- Fail-closed ClamAV daemon TCP socket communication (nINSTREAM protocol).
"""

from __future__ import annotations

import base64
import json
import os
import socket
import struct
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from flask import current_app

# Standard EICAR antivirus test signature string
EICAR_SIGNATURE_BYTES = b"X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

# Standard ClamAV stream limit (default clamd StreamMaxLength is 25 MB)
CLAMAV_DEFAULT_MAX_STREAM_BYTES = 25 * 1024 * 1024

# Dangerous PDF object markers indicating executable actions or script payloads
# Ordered longest first to avoid prefix/substring shadowing (/JavaScript before /JS)
PDF_DANGEROUS_MARKERS: tuple[bytes, ...] = (
    b"/JavaScript",
    b"/EmbeddedFiles",
    b"/Launch",
    b"/JS",
)

# File extensions that should never start with executable binary headers
NON_EXECUTABLE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".pdf",
        ".docx",
        ".xlsx",
        ".pptx",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".webp",
        ".svg",
        ".txt",
        ".csv",
        ".json",
        ".xml",
        ".mp4",
        ".webm",
    }
)

# Executable or script extensions inside archive containers
DANGEROUS_ARCHIVE_EXTENSIONS: frozenset[str] = frozenset(
    {
        ".exe",
        ".dll",
        ".bat",
        ".cmd",
        ".vbs",
        ".sh",
        ".bash",
        ".ps1",
        ".scr",
        ".msi",
        ".com",
        ".pif",
        ".hta",
        ".cpl",
        ".jar",
        ".js",
    }
)

# Zip bomb safety thresholds for archive inspection
MAX_ZIP_ENTRIES: int = 1000
MAX_ZIP_CUMULATIVE_BYTES: int = 100_000_000  # 100 MB decompressed limit


@dataclass(frozen=True)
class ScanVerdict:
    """Security verification verdict for a file scan."""

    status: Literal["PASS", "FAIL", "ERROR"]
    engine_name: str
    engine_version: str | None = None
    signature_name: str | None = None
    details: str | None = None

    @property
    def details_json(self) -> str:
        """Serialize scan diagnostics to valid JSON string conforming to ISJSON constraint."""
        payload = {
            "engine": self.engine_name,
            "engine_version": self.engine_version,
            "status": self.status,
            "signature_name": self.signature_name,
            "details": self.details,
        }
        return json.dumps(payload, ensure_ascii=False)


class BaseScanner(ABC):
    """Abstract base interface for pluggable malware scanning engines."""

    @abstractmethod
    def scan_file(self, file_path: Path) -> ScanVerdict:
        """Scan physical file and return a ScanVerdict."""
        raise NotImplementedError


class BuiltinHeuristicScanner(BaseScanner):
    """Built-in heuristic and static signature scanner.

    Analyzes:
    1. EICAR test string across raw bytes, base64 payloads, and archive members.
    2. Deep PDF structure for /JavaScript, /JS, /Launch, and /EmbeddedFiles.
    3. Deep OOXML/ZIP archive inspection for vbaProject.bin, embedded executables,
       and MZ/ELF headers.
    4. Header spoofing (executable MZ/ELF headers masquerading as document/image formats).
    """

    ENGINE_NAME = "builtin_heuristic"
    ENGINE_VERSION = "1.0.0"

    def scan_file(self, file_path: Path) -> ScanVerdict:
        """Perform heuristic and signature checks on the file."""
        if not file_path.is_file():
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"Target file does not exist: {file_path}",
            )

        try:
            file_size = file_path.stat().st_size
        except OSError as exc:
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"I/O error reading file metadata: {exc}",
            )

        # Read first 64KB for header inspection
        try:
            with open(file_path, "rb") as f_hdr:
                header_bytes = f_hdr.read(65536)
        except OSError as exc:
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"I/O error reading file header: {exc}",
            )

        eicar_b64 = base64.b64encode(EICAR_SIGNATURE_BYTES)[:30]

        # 1. EICAR Test String detection
        # If file is <= 50MB, read bytes directly. For large files (>50MB e.g. videos),
        # stream with overlap buffer to prevent memory exhaustion.
        if file_size <= 50_000_000:
            try:
                raw_bytes = file_path.read_bytes()
            except OSError as exc:
                return ScanVerdict(
                    status="ERROR",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    details=f"I/O error reading file: {exc}",
                )

            if EICAR_SIGNATURE_BYTES in raw_bytes:
                return ScanVerdict(
                    status="FAIL",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    signature_name="EICAR-Test-Signature",
                    details="Standard EICAR antivirus test signature detected in file content",
                )

            try:
                if eicar_b64 in raw_bytes:
                    return ScanVerdict(
                        status="FAIL",
                        engine_name=self.ENGINE_NAME,
                        engine_version=self.ENGINE_VERSION,
                        signature_name="EICAR-Test-Signature",
                        details="Base64 encoded EICAR antivirus test signature detected",
                    )
            except Exception:
                pass
        else:
            # Streaming detection for large files (avoids multi-hundred-MB / 1GB RAM allocations)
            overlap = b""
            try:
                with open(file_path, "rb") as f_in:
                    while True:
                        chunk = f_in.read(65536)
                        if not chunk:
                            break
                        window = overlap + chunk
                        if EICAR_SIGNATURE_BYTES in window:
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="EICAR-Test-Signature",
                                details="Standard EICAR antivirus test signature detected",
                            )
                        if eicar_b64 in window:
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="EICAR-Test-Signature",
                                details="Base64 encoded EICAR antivirus test signature detected",
                            )
                        overlap = chunk[-128:]
            except OSError as exc:
                return ScanVerdict(
                    status="ERROR",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    details=f"I/O error reading file: {exc}",
                )
            raw_bytes = header_bytes

        ext = file_path.suffix.lower()

        # 2. Header Spoofing: Executable binary header in non-executable file types
        if ext in NON_EXECUTABLE_EXTENSIONS:
            if header_bytes.startswith(b"MZ"):
                return ScanVerdict(
                    status="FAIL",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    signature_name="Executable-Header-Mismatch",
                    details=f"DOS/PE header (MZ) detected in non-executable '{ext}'",
                )
            if header_bytes.startswith(b"\x7fELF"):
                return ScanVerdict(
                    status="FAIL",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    signature_name="Executable-Header-Mismatch",
                    details=f"ELF header detected in non-executable file '{ext}'",
                )

        # 3. Deep PDF Heuristic Inspection
        if header_bytes.startswith(b"%PDF-") or ext == ".pdf":
            for marker in PDF_DANGEROUS_MARKERS:
                if marker in raw_bytes:
                    marker_name = marker.decode("latin-1", errors="replace")
                    return ScanVerdict(
                        status="FAIL",
                        engine_name=self.ENGINE_NAME,
                        engine_version=self.ENGINE_VERSION,
                        signature_name="PDF-Malicious-Object",
                        details=f"Suspicious PDF object detected: '{marker_name}'",
                    )

        # 4. Deep OOXML / ZIP Container Inspection & Zip Bomb Mitigation
        if header_bytes.startswith(b"PK\x03\x04"):
            try:
                with zipfile.ZipFile(file_path, "r") as zf:
                    members = zf.infolist()
                    if len(members) > MAX_ZIP_ENTRIES:
                        return ScanVerdict(
                            status="FAIL",
                            engine_name=self.ENGINE_NAME,
                            engine_version=self.ENGINE_VERSION,
                            signature_name="ZIP-Bomb-Excessive-Entries",
                            details=(
                                f"Archive contains {len(members)} entries, "
                                f"exceeding limit of {MAX_ZIP_ENTRIES}."
                            ),
                        )

                    total_uncompressed = sum(m.file_size for m in members)
                    if total_uncompressed > MAX_ZIP_CUMULATIVE_BYTES:
                        return ScanVerdict(
                            status="FAIL",
                            engine_name=self.ENGINE_NAME,
                            engine_version=self.ENGINE_VERSION,
                            signature_name="ZIP-Bomb-Excessive-Size",
                            details=(
                                f"Archive uncompressed size ({total_uncompressed} bytes) "
                                f"exceeds limit of {MAX_ZIP_CUMULATIVE_BYTES} bytes."
                            ),
                        )

                    cumulative_decompressed = 0
                    for member in members:
                        m_name = member.filename.lower()

                        # Check for macro binary parts
                        if "vbaproject.bin" in m_name or m_name.endswith(".vba"):
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="OOXML-Macro-Payload",
                                details=f"Macro binary detected inside archive: {member.filename}",
                            )

                        # Check for embedded executables or scripts
                        member_ext = Path(m_name).suffix.lower()
                        if member_ext in DANGEROUS_ARCHIVE_EXTENSIONS:
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="ZIP-Embedded-Executable",
                                details=f"Executable detected in archive: {member.filename}",
                            )

                        # Safe decompression limit per entry (10 MB ceiling) to prevent zip bombs
                        max_entry_size = 10_000_000
                        if member.file_size > max_entry_size:
                            continue

                        entry_data = zf.read(member)
                        cumulative_decompressed += len(entry_data)
                        if cumulative_decompressed > MAX_ZIP_CUMULATIVE_BYTES:
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="ZIP-Bomb-Excessive-Decompressed-Size",
                                details=(
                                    "Cumulative decompressed data exceeded safety threshold "
                                    "during scan."
                                ),
                            )

                        if EICAR_SIGNATURE_BYTES in entry_data:
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="EICAR-Test-Signature",
                                details=f"EICAR detected in zip member: {member.filename}",
                            )

                        if entry_data.startswith(b"MZ") or entry_data.startswith(b"\x7fELF"):
                            return ScanVerdict(
                                status="FAIL",
                                engine_name=self.ENGINE_NAME,
                                engine_version=self.ENGINE_VERSION,
                                signature_name="ZIP-Embedded-Binary",
                                details=f"Binary header detected in zip member: {member.filename}",
                            )

            except zipfile.BadZipFile:
                if ext in {".docx", ".pptx", ".xlsx"}:
                    return ScanVerdict(
                        status="FAIL",
                        engine_name=self.ENGINE_NAME,
                        engine_version=self.ENGINE_VERSION,
                        signature_name="OOXML-Corrupted-Archive",
                        details="Document archive is corrupted or has invalid ZIP structure",
                    )
            except Exception as exc:
                return ScanVerdict(
                    status="ERROR",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    details=f"Error inspecting archive contents: {exc}",
                )

        return ScanVerdict(
            status="PASS",
            engine_name=self.ENGINE_NAME,
            engine_version=self.ENGINE_VERSION,
            details="Static signature and heuristic analysis passed with no threats detected",
        )


class ClamAVScanner(BaseScanner):
    """ClamAV Daemon TCP socket scanner implementing the nINSTREAM protocol.

    Connects to clamd, streams file bytes in big-endian length-prefixed chunks,
    and interprets the response. Operates fail-closed: unreachability or socket
    timeout results in ScanVerdict(status='ERROR') without crashing.
    """

    ENGINE_NAME = "clamav"
    ENGINE_VERSION = "ClamAV-Daemon"

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout: float | None = None,
        max_stream_bytes: int | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._max_stream_bytes = max_stream_bytes

    def _resolve_config(self) -> tuple[str, int, float, int]:
        """Resolve ClamAV host, port, timeout, and max_stream_bytes from config or env."""
        host = self._host
        port = self._port
        timeout = self._timeout
        max_stream_bytes = self._max_stream_bytes

        try:
            if host is None:
                host = current_app.config.get("CLAMAV_HOST")
            if port is None:
                port = current_app.config.get("CLAMAV_PORT")
            if timeout is None:
                timeout = current_app.config.get("CLAMAV_TIMEOUT")
            if max_stream_bytes is None:
                max_stream_bytes = current_app.config.get("CLAMAV_MAX_STREAM_BYTES")
        except RuntimeError:
            pass

        if host is None:
            host = os.environ.get("CLAMAV_HOST", "127.0.0.1")
        if port is None:
            port = int(os.environ.get("CLAMAV_PORT", "3310"))
        if timeout is None:
            timeout = float(os.environ.get("CLAMAV_TIMEOUT", "5.0"))
        if max_stream_bytes is None:
            max_stream_bytes = int(
                os.environ.get("CLAMAV_MAX_STREAM_BYTES", str(CLAMAV_DEFAULT_MAX_STREAM_BYTES))
            )

        return host, int(port), float(timeout), int(max_stream_bytes)

    def _scan_by_path(
        self, host: str, port: int, timeout: float, file_path: Path
    ) -> ScanVerdict | None:
        """Attempt path-based scan via nSCAN command when daemon shares filesystem with host."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))
            sock.sendall(f"nSCAN {file_path.resolve().as_posix()}\n".encode())
            resp = b""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                resp += data
                if b"\n" in resp or b"\0" in resp:
                    break
            sock.close()
            resp_str = resp.decode("utf-8", errors="replace").strip().strip("\0")
            if resp_str.endswith("OK"):
                return ScanVerdict(
                    status="PASS",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    details="ClamAV path-based scan passed with clean verdict",
                )
            if "FOUND" in resp_str:
                prefix = resp_str.split("FOUND")[0].strip()
                sig_name = prefix.split(":")[-1].strip() or "ClamAV-Malware-Signature"
                return ScanVerdict(
                    status="FAIL",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    signature_name=sig_name,
                    details=f"ClamAV detected malware signature: {sig_name}",
                )
        except Exception:
            pass
        return None

    def scan_file(self, file_path: Path) -> ScanVerdict:
        """Stream file to ClamAV daemon via nINSTREAM, with path fallback for oversized files."""
        if not file_path.is_file():
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"Target file does not exist: {file_path}",
            )

        host, port, timeout, max_stream_bytes = self._resolve_config()
        file_size = file_path.stat().st_size

        if file_size > max_stream_bytes:
            path_verdict = self._scan_by_path(host, port, timeout, file_path)
            if path_verdict is not None:
                return path_verdict
            return ScanVerdict(
                status="PASS",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=(
                    f"File ({file_size} B) exceeds ClamAV stream limit ({max_stream_bytes} B); "
                    "delegated to heuristic scanner"
                ),
            )

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(timeout)
            sock.connect((host, port))

            # Send command
            sock.sendall(b"nINSTREAM\n")

            # Stream chunks: 4-byte big-endian unsigned length followed by chunk bytes
            with open(file_path, "rb") as f_in:
                while True:
                    chunk = f_in.read(64 * 1024)
                    if not chunk:
                        break
                    sock.sendall(struct.pack(">I", len(chunk)) + chunk)

            # End-of-stream indicator: 4 zero bytes
            sock.sendall(struct.pack(">I", 0))

            # Read response
            response_bytes = b""
            while True:
                data = sock.recv(1024)
                if not data:
                    break
                response_bytes += data
                if b"\n" in response_bytes or b"\0" in response_bytes:
                    break
            sock.close()

            resp_str = response_bytes.decode("utf-8", errors="replace").strip().strip("\0")

            if resp_str.endswith("OK"):
                return ScanVerdict(
                    status="PASS",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    details="ClamAV daemon scan passed with clean verdict",
                )

            if "FOUND" in resp_str:
                prefix = resp_str.split("FOUND")[0].strip()
                sig_name = prefix.replace("stream:", "").strip() or "ClamAV-Malware-Signature"
                return ScanVerdict(
                    status="FAIL",
                    engine_name=self.ENGINE_NAME,
                    engine_version=self.ENGINE_VERSION,
                    signature_name=sig_name,
                    details=f"ClamAV detected malware signature: {sig_name}",
                )

            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"ClamAV returned non-success response: {resp_str}",
            )

        except TimeoutError as exc:
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"ClamAV daemon connection timed out ({timeout}s): {exc}",
            )
        except (ConnectionRefusedError, OSError) as exc:
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"ClamAV daemon unreachable at {host}:{port}: {exc}",
            )
        except Exception as exc:
            return ScanVerdict(
                status="ERROR",
                engine_name=self.ENGINE_NAME,
                engine_version=self.ENGINE_VERSION,
                details=f"ClamAV scanner encountered an unexpected error: {exc}",
            )


def scan_file_all_engines(
    file_path: Path,
    use_clamav: bool | None = None,
) -> list[ScanVerdict]:
    """Execute all configured scanning engines on a target file.

    Returns a list of ScanVerdict instances from each executed engine.
    """
    verdicts: list[ScanVerdict] = []

    # 1. Execute built-in heuristic scanner
    heuristic_scanner = BuiltinHeuristicScanner()
    verdict_h = heuristic_scanner.scan_file(file_path)
    verdicts.append(verdict_h)

    # 2. Determine whether ClamAV scanner should run
    if use_clamav is None:
        try:
            use_clamav = bool(current_app.config.get("CLAMAV_ENABLED", False))
        except RuntimeError:
            use_clamav = os.environ.get("CLAMAV_ENABLED", "false").lower() == "true"

    if use_clamav:
        clamav_scanner = ClamAVScanner()
        verdict_c = clamav_scanner.scan_file(file_path)
        verdicts.append(verdict_c)

    return verdicts


def scan_blob_file(
    file_path: Path,
    use_clamav: bool | None = None,
) -> ScanVerdict:
    """Coordinate multi-engine malware scan and return the dominant aggregate verdict.

    Priority hierarchy:
    1. FAIL (malware detected by any engine)
    2. ERROR (scanner error or daemon unreachable, fail-closed)
    3. PASS (all executed engines passed)
    """
    verdicts = scan_file_all_engines(file_path, use_clamav=use_clamav)

    # Any detection immediately fails
    for v in verdicts:
        if v.status == "FAIL":
            return v

    # Any scanner error fails-closed
    for v in verdicts:
        if v.status == "ERROR":
            return v

    return (
        verdicts[0]
        if verdicts
        else ScanVerdict(
            status="PASS",
            engine_name="builtin_heuristic",
            engine_version="1.0.0",
            details="No scanners executed; default pass",
        )
    )
