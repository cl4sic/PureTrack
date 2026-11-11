#!/usr/bin/env python3
"""
pipeline.py - Orquestador Integral de Auditoría, Enriquecimiento y Ejecución Segura.

Fase 3 del Pipeline de Sanación y Organización de Audio MP3.
Coordina:
1. Fase 1: Auditoría Técnica y Diagnóstico (audit_audio.py).
2. Fase 2: Identificación Web y Normalización de Metadatos (enrich_metadata.py).
3. Fase 3: Ejecución Segura con dry-run por defecto, registro en output/rename_log.json y capacidad de rollback.

100% compatible con Windows NTFS (pathlib.Path, saneamiento de caracteres y codificación UTF-8).
"""

import sys
import os

# Auto-reexecutar con el entorno virtual si se invoca con el python del sistema sin dependencias (en desarrollo)
if not getattr(sys, "frozen", False):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_python = os.path.join(script_dir, ".venv", "bin", "python")
    if os.path.exists(venv_python) and sys.executable != venv_python:
        try:
            import mutagen
        except ImportError:
            os.execv(venv_python, [venv_python] + sys.argv)

from pathlib import Path
import json
import shutil
import argparse
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Optional, Union

from common_utils import resolve_binary, sanitize_windows_filename
from audit_audio import AudioAuditor, export_csv, export_markdown
from enrich_metadata import MetadataEnricher, ResolvedMetadata


DEFAULT_LOG_PATH = "output/rename_log.json"


class SafePipeline:
    """Orquestador seguro del ciclo de vida de audio con soporte nativo de Windows."""

    def __init__(self, directory: Union[str, Path] = ".", log_file: Union[str, Path] = DEFAULT_LOG_PATH):
        self.directory = Path(directory).resolve()
        self.output_dir = self.directory / "output"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = Path(log_file)
        if not self.log_file.is_absolute():
            self.log_file = self.directory / self.log_file
        self.log_file.parent.mkdir(parents=True, exist_ok=True)

        self.auditor = AudioAuditor(search_dir=self.directory)
        self.enricher = MetadataEnricher(search_dir=self.directory)
        self.ffmpeg_bin = resolve_binary("ffmpeg", search_dir=self.directory)

    def run_phase1_audit(
        self,
        output_md: Union[str, Path] = "informe_auditoria.md",
        output_csv: Union[str, Path] = "informe_auditoria.csv"
    ) -> List[Any]:
        """Ejecuta la Fase 1: Auditoría técnica y diagnóstico pasivo con pathlib.Path."""
        print("\n" + "=" * 70)
        print(">>> INICIANDO FASE 1: AUDITORÍA TÉCNICA Y DIAGNÓSTICO")
        print("=" * 70)

        mp3_files = sorted(self.directory.glob("*.mp3"))
        if not mp3_files:
            print(f"[!] No se encontraron archivos MP3 en {self.directory}")
            return []

        results = []
        for idx, fpath in enumerate(mp3_files, 1):
            fname = fpath.name
            print(f"  [{idx}/{len(mp3_files)}] Auditando integridad acústica: {fname}")
            res = self.auditor.audit_file(fpath)
            results.append(res)
            print(f"      -> Bitrate: {res.mutagen_bitrate_kbps} kbps ({res.bitrate_mode}) | Duración: {res.duration_sec}s | Veredicto: [{res.verdict}]")

        md_targets = [self.directory / output_md, self.output_dir / output_md]
        csv_targets = [self.directory / output_csv, self.output_dir / output_csv]

        for p in csv_targets:
            export_csv(results, p)
        for p in md_targets:
            export_markdown(results, p)

        print("\n[+] Fase 1 completada con éxito.")
        print(f"    - Informe Markdown: {md_targets[0]} (y copia en {md_targets[1]})")
        print(f"    - Informe CSV:      {csv_targets[0]} (y copia en {csv_targets[1]})")
        return results

    def run_phase2_and_3(self, audit_results: List[Any], dry_run: bool = True):
        """
        Ejecuta la Fase 2 (Enriquecimiento) y Fase 3 (Ejecución Segura con dry-run/apply).
        Solo procesa archivos calificados como APTA o bajo aprobación.
        """
        print("\n" + "=" * 70)
        mode_label = "MODO SIMULACIÓN (DRY-RUN - SIN MODIFICAR ARCHIVOS)" if dry_run else "MODO EJECUCIÓN REAL (APPLY)"
        print(f">>> INICIANDO FASE 2 & 3: NORMALIZACIÓN Y EJECUCIÓN SEGURA [{mode_label}]")
        print("=" * 70)

        valid_files = [Path(r.filepath) for r in audit_results if r.verdict == "APTA"]
        skipped_files = [r for r in audit_results if r.verdict != "APTA"]

        if skipped_files:
            print(f"[!] {len(skipped_files)} pistas omitidas por no superar el criterio de calidad:")
            for s in skipped_files:
                print(f"    - {s.filename}: [{s.verdict}] {s.verdict_reason}")

        if not valid_files:
            print("[!] No hay pistas aptas para enriquecimiento.")
            return

        actions = []
        for idx, fpath in enumerate(valid_files, 1):
            fname = fpath.name
            resolved = self.enricher.resolve_track_metadata(fpath)
            old_tags = self.enricher.extract_current_tags(fpath)

            new_tags = {
                "TIT2": resolved.id3_tit2,
                "TPE1": resolved.id3_tpe1,
                "TALB": resolved.id3_talb,
                "TPE2": resolved.id3_tpe2,
                "TCON": resolved.id3_tcon,
                "TDRC": resolved.id3_tdrc or "",
            }

            dest_path = self.directory / resolved.new_filename

            action_record = {
                "original_path": str(fpath),
                "original_filename": fname,
                "new_path": str(dest_path),
                "new_filename": resolved.new_filename,
                "old_tags": old_tags,
                "new_tags": new_tags,
                "source": resolved.source,
                "executed": not dry_run,
            }
            actions.append((resolved, action_record))

            print(f"\n  [{idx}/{len(valid_files)}] Propuesta de normalización (Saneada para Windows):")
            print(f"    Original : {fname}")
            print(f"    Destino  : {resolved.new_filename}")
            print(f"    ID3 TIT2 : {resolved.id3_tit2}")
            print(f"    ID3 TPE1 : {resolved.id3_tpe1}")
            print(f"    ID3 TALB : {resolved.id3_talb}")
            print(f"    ID3 TPE2 : {resolved.id3_tpe2}")
            print(f"    ID3 TCON : {resolved.id3_tcon}")
            print(f"    ID3 TDRC : {resolved.id3_tdrc}")

        manifest_payload = {
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run,
            "total_items": len(actions),
            "operations": [record for _, record in actions],
        }

        if dry_run:
            print("\n" + "-" * 70)
            print("[SIMULACIÓN] No se aplicaron modificaciones sobre los archivos MP3.")
            print("Para aplicar los cambios reales de forma permanente, ejecute:")
            print("    python pipeline.py --apply")
            print("-" * 70)
        else:
            print("\n[*] Aplicando modificaciones reales en el sistema de archivos...")
            # 1. Guardar log de respaldo ANTES de mover o modificar
            with open(self.log_file, "w", encoding="utf-8") as f:
                json.dump(manifest_payload, f, indent=2, ensure_ascii=False)

            root_log = self.directory / "rename_log.json"
            with open(root_log, "w", encoding="utf-8") as f:
                json.dump(manifest_payload, f, indent=2, ensure_ascii=False)

            print(f"[+] Manifiesto de respaldo guardado en:")
            print(f"    - {self.log_file}")
            print(f"    - {root_log}")

            # 2. Aplicar etiquetas ID3v2 y luego renombrar
            success_count = 0
            for resolved, record in actions:
                src_path = Path(record["original_path"])
                dst_path = Path(record["new_path"])

                tag_ok = self.enricher.apply_id3_tags(src_path, resolved)
                if not tag_ok:
                    print(f"[!] Fallo al escribir tags en {src_path.name}. Operación abortada para esta pista.")
                    continue

                if src_path != dst_path:
                    try:
                        shutil.move(str(src_path), str(dst_path))
                        success_count += 1
                        print(f"  [OK] Renombrado: {record['original_filename']} -> {record['new_filename']}")
                    except Exception as e:
                        print(f"[!] Error al renombrar {src_path.name} a {dst_path.name}: {e}")
                else:
                    success_count += 1
                    print(f"  [OK] Tags actualizados: {record['original_filename']}")

            print(f"\n[+] Proceso finalizado. {success_count}/{len(actions)} archivos actualizados y renombrados.")

            # 3. Confirmación de Integridad Post-Modificación
            print("\n" + "=" * 70)
            print(">>> VALIDACIÓN DE INTEGRIDAD Y CONFIRMACIÓN DE DISCO POST-EJECUCIÓN")
            print("=" * 70)
            all_intact = True
            for _, record in actions:
                target = Path(record["new_path"])
                if not target.exists():
                    print(f"  [ERROR] No se encuentra el archivo renombrado: {target.name}")
                    all_intact = False
                    continue

                res = subprocess.run([self.ffmpeg_bin, "-v", "error", "-i", str(target), "-f", "null", "-"], capture_output=True, text=True)
                if res.returncode != 0 or res.stderr.strip():
                    print(f"  [ERROR CORRUPCIÓN] {target.name}: {res.stderr.strip()}")
                    all_intact = False
                else:
                    print(f"  [VERIFICADO - ÍNTEGRO] {record['new_filename']} (ID3v2 tags aplicadas, audio intacto)")

            if all_intact:
                print("\n[+] Todos los archivos se encuentran en perfecto estado sin corrupción.")
            print(f"    En caso de requerir reversión instantánea, ejecute: python pipeline.py --rollback")

    def rollback(self):
        """Restaura los nombres y etiquetas originales utilizando el log de operaciones."""
        print("\n" + "=" * 70)
        print(">>> INICIANDO ROLLBACK (RESTAURACIÓN DE SEGURIDAD)")
        print("=" * 70)

        candidates = [self.log_file, self.directory / "rename_log.json"]
        chosen_log = None
        for cand in candidates:
            if cand.exists():
                chosen_log = cand
                break

        if not chosen_log:
            print(f"[!] No se encontró ningún archivo de registro para realizar el rollback.")
            return False

        with open(chosen_log, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        operations = manifest.get("operations", [])
        if not operations:
            print("[!] El archivo de registro no contiene operaciones para restaurar.")
            return False

        print(f"[*] Restaurando {len(operations)} archivos según registro de {manifest.get('timestamp')} ({chosen_log})...")

        from mutagen.id3 import ID3, TIT2, TPE1, TALB, TPE2, TCON, TDRC

        restored_count = 0
        for op in operations:
            orig_path = Path(op["original_path"])
            new_path = Path(op["new_path"])
            old_tags = op.get("old_tags", {})

            target_path = orig_path
            if new_path.exists() and new_path != orig_path:
                try:
                    shutil.move(str(new_path), str(orig_path))
                    target_path = orig_path
                    print(f"  [OK] Archivo renombrado de vuelta a: {op['original_filename']}")
                except Exception as e:
                    print(f"  [!] Error revirtiendo nombre de {new_path.name}: {e}")
                    target_path = new_path

            if target_path.exists() and old_tags:
                try:
                    tags = ID3(str(target_path))
                    if "TIT2" in old_tags:
                        tags.setall("TIT2", [TIT2(encoding=3, text=old_tags["TIT2"])])
                    if "TPE1" in old_tags:
                        tags.setall("TPE1", [TPE1(encoding=3, text=old_tags["TPE1"])])
                    if "TALB" in old_tags:
                        tags.setall("TALB", [TALB(encoding=3, text=old_tags["TALB"])])
                    if "TPE2" in old_tags:
                        tags.setall("TPE2", [TPE2(encoding=3, text=old_tags["TPE2"])])
                    if "TCON" in old_tags:
                        tags.setall("TCON", [TCON(encoding=3, text=old_tags["TCON"])])
                    if "TDRC" in old_tags:
                        tags.setall("TDRC", [TDRC(encoding=3, text=old_tags["TDRC"])])
                    tags.save(str(target_path), v2_version=3)
                    print(f"  [OK] Tags originales restaurados en: {target_path.name}")
                    restored_count += 1
                except Exception as e:
                    print(f"  [!] Error restaurando tags en {target_path.name}: {e}")
            else:
                restored_count += 1

        print(f"\n[+] Rollback completado. {restored_count}/{len(operations)} archivos restaurados.")
        return True


def main():
    parser = argparse.ArgumentParser(description="Pipeline Integral de Sanación y Organización de Colección de Audio MP3 (Multiplataforma)")
    parser.add_argument("--dir", default=".", help="Directorio con archivos MP3 (defecto: actual)")
    parser.add_argument("--phase", choices=["audit", "enrich", "all"], default="all", help="Fase a ejecutar")
    parser.add_argument("--apply", action="store_true", help="Aplica los cambios reales de renombrado y tags (por defecto es dry-run)")
    parser.add_argument("--rollback", action="store_true", help="Revierte todos los cambios a partir del registro")
    parser.add_argument("--log", default=DEFAULT_LOG_PATH, help="Ruta del archivo de registro (defecto: output/rename_log.json)")
    args = parser.parse_args()

    pipeline = SafePipeline(directory=args.dir, log_file=args.log)

    if args.rollback:
        pipeline.rollback()
        return

    if args.phase in ["audit", "all"]:
        audit_results = pipeline.run_phase1_audit()
    else:
        auditor = AudioAuditor(search_dir=args.dir)
        audit_results = [auditor.audit_file(f) for f in sorted(Path(args.dir).glob("*.mp3"))]

    if args.phase in ["enrich", "all"]:
        dry_run = not args.apply
        pipeline.run_phase2_and_3(audit_results, dry_run=dry_run)


if __name__ == "__main__":
    main()
