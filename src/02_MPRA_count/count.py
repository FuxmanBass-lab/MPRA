#!/usr/bin/env python3
import argparse, subprocess, os, sys

def run(cmd, stdout=None):
    print(f">> {cmd}", file=sys.stderr)
    subprocess.run(cmd, shell=True, check=True, stdout=stdout)

def main():
    p = argparse.ArgumentParser(description="MPRA replicate‐counting pipeline")
    p.add_argument("--replicate_fastq",  required=True,
                   help="Comma‐separated list of replicate FASTQ files")
    p.add_argument("--replicate_id",     required=True,
                   help="Comma‐separated list of replicate IDs (same order)")
    p.add_argument("--parsed",           required=True,
                   help="Parsed output from match pipeline")
    p.add_argument("--acc_id",           required=True,
                   help="Path to replicate index (acc_id)")
    p.add_argument("--barcode_orientation", type=int, default=2,
                   help="2 if match used read_a=R1, else 1")
    p.add_argument("--bc_len",           type=int, default=20,
                   help="Barcode length")
    p.add_argument("--flags",            default="-ECSM -A 0.05",
                   help="Flags for compile_bc_cs")
    p.add_argument("--scripts_dir",      required=True,
                   help="Where helper scripts live")
    p.add_argument("--out_dir",          required=True,
                   help="Directory to write outputs")
    p.add_argument("--id_out",           required=True,
                   help="Project identifier prefix")
    args = p.parse_args()

    # prepare workspace
    os.makedirs(args.out_dir, exist_ok=True)
    os.chdir(args.out_dir)

    fastqs = args.replicate_fastq.split(",")
    ids    = args.replicate_id.split(",")
    if len(fastqs) != len(ids):
        raise ValueError(f"replicate_fastq and replicate_id must have same length (got {len(fastqs)} fastqs, {len(ids)} ids)")

    tag_files = []
    tag_ids   = []

    # ── scatter: prep_counts & associate ──────────────────────────────────────

    for fq, sid in zip(fastqs, ids):
        # 1) prep_counts → {sid}.match
        
        run(
            f"python3 {args.scripts_dir}/make_counts.py "
            f"{fq} {sid} {args.barcode_orientation} {args.bc_len}"
        )
        match_f = f"{sid}.match"


        # 2) associate → {sid}.tag

        run(
            f"python3 {args.scripts_dir}/associate_tags.py "
            f"{match_f} {args.parsed} {sid}.tag {args.barcode_orientation}"
        )
        tag_files.append(f"{sid}.tag")
        tag_ids.append(sid)


        
    # ── make_infile ──────────────────────────────────────────────────────────

    run(
        f"python3 {args.scripts_dir}/make_infile.py "
        f"{','.join(tag_ids)} {','.join(tag_files)} {args.id_out}"
    )

    
    samples_txt = f"{args.id_out}_samples.txt"

    # Check existence of samples file
    if not os.path.exists(samples_txt):
        raise FileNotFoundError(
            f"Expected samples file {samples_txt} not found. Please regenerate or uncomment the make_infile step."
        )

    # Check all tag files exist
    for sid in ids:
        tag_file = f"{sid}.tag"
        if not os.path.exists(tag_file):
            raise FileNotFoundError(
                f"Expected tag file {tag_file} not found. Please regenerate or uncomment associate_tags step."
            )

    # ── make_count_table ─────────────────────────────────────────────────────
    count_f = f"{args.id_out}.count"
    stats_f = f"{args.id_out}.stats"


    # compile barcodes + cs into count file
    flag_list = args.flags.strip().split()
    compile_cmd = (
        f"python3 {args.scripts_dir}/compile_bc_cs.py "
        + " ".join(flag_list)
        + f" {samples_txt} {count_f}"
    )
    run(compile_cmd)

    # AWK step to create stats file with header
    awk_cmd = (
        "awk 'BEGIN { print \"Sample\\tKey\\tCount\\tSum\" } "
        "/Summary for sample=/ {"
        " match($0, /sample=([^,]+)/, a);"
        " match($0, /key=([^:]+)/, b);"
        " match($0, /count=([0-9]+)/, c);"
        " match($0, /sum=([0-9]+)/, d);"
        " if (a[1] != \"\" && b[1] != \"\" && c[1] != \"\" && d[1] != \"\") {"
        " printf \"%s\\t%s\\t%s\\t%s\\n\", a[1], b[1], c[1], d[1];"
        " }"
        " }' "
        + count_f + ".log > " + stats_f
    )
    run(awk_cmd)



    # 4) read_stats.py (replaces Rscript read_stats.R)
    run(
        f"python3 {args.scripts_dir}/read_stats.py "
        f"{stats_f} {args.acc_id} {args.id_out} {args.out_dir}"
    )

    # 5) count_QC → {id_out}_condition.txt
    cond_f = f"{args.id_out}_condition.txt"
    run(
        f"python3 {args.scripts_dir}/count_qc.py "
        f"{args.acc_id} {count_f} {args.id_out} {args.out_dir}"
    )

    # 6) countRaw → cell‐type specific counts
    run(
        f"python3 {args.scripts_dir}/bc_raw.py "
        f"{cond_f} {count_f} {args.id_out} {args.out_dir}"
    )

    # 7) relocate all artifacts
    to_move = []
    # prep_counts outputs
    for sid in ids:
        to_move.append(f"{sid}.match")
    # associate outputs
    for sid in ids:
        to_move.append(f"{sid}.tag")
    # count      
    to_move += [count_f, stats_f, cond_f]
    for fn in to_move:
        src = os.path.abspath(fn)
        dst = os.path.abspath(os.path.join(args.out_dir, os.path.basename(fn)))
        if src != dst:
            run(f"mv {fn} {args.out_dir}/")
        else:
            print(f"Skipping move for {fn}, already in {args.out_dir}/", file=sys.stderr)

if __name__ == "__main__":
    main()
