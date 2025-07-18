#!/usr/bin/env python3
import argparse, subprocess, os, sys

def run(cmd):
    print(f">> {cmd}", file=sys.stderr)
    subprocess.run(cmd, shell=True, check=True)

def main():
    p = argparse.ArgumentParser(description="MPRA barcode–oligo matching pipeline")
    p.add_argument("--read_a",         required=True,  help="R1 FASTQ")
    p.add_argument("--read_b",         required=True,  help="R2 FASTQ")
    p.add_argument("--reference_fasta",required=True,  help="Oligo reference FASTA")
    p.add_argument("--attributes",     help="(optional) saturation mut. attributes")
    p.add_argument("--barcode_orientation", type=int, default=2)
    p.add_argument("--threads",        type=int, default=30)
    p.add_argument("--mem",            type=int, default=30)
    p.add_argument("--read_len",       type=int, default=250)
    p.add_argument("--frag_len",       type=int, default=274)
    p.add_argument("--seq_min",        type=int, default=100)
    p.add_argument("--enh_min",        type=int, default=50)
    p.add_argument("--enh_max",        type=int, default=210)
    p.add_argument("--bc_len",         type=int, default=20)
    p.add_argument("--bc_link_size",   type=int, default=38)
    p.add_argument("--end_link_size",  type=int, default=16)
    p.add_argument("--barcode_link",   default="TCTAGA")
    p.add_argument("--oligo_link",     default="AGTG")
    p.add_argument("--end_oligo_link", default="CGTC")
    p.add_argument("--oligo_alnmismatchrate_cutoff", type=float, default=0.05,
                   help="Maximum allowed oligo alignment mismatch rate (default 0.05)")
    p.add_argument("--scripts_dir",    required=True, help="where pull_barcodes.py etc live")
    p.add_argument("--out_dir",        required=True, help="where to write all results")
    p.add_argument("--id_out",         required=True, help="output prefix (id_out)")
    args = p.parse_args()

    #  ─── prepare output ───────────────────────────────────────────────────────
    os.makedirs(args.out_dir, exist_ok=True)
    os.chdir(args.out_dir)

    # 1) FLASH
    prefix = f"{args.id_out}.merged"
    run(f"flash2 -r {args.read_len} -f {args.frag_len} -s 25 -o {prefix} -t {args.threads} {args.read_a} {args.read_b}")
    flash_out = f"{prefix}.extendedFrags.fastq"

    # 2) Pull barcodes
    run(
        f"python3 {args.scripts_dir}/pull_barcodes.py "
        f"{flash_out} {args.barcode_orientation} {args.id_out}.merged "
        f"{args.barcode_link} {args.oligo_link} {args.end_oligo_link} "
        f"{args.seq_min} {args.enh_min} {args.enh_max} "
        f"{args.bc_len} {args.bc_link_size} {args.end_link_size}"
    )
    match_f = f"{args.id_out}.merged.match"
    reject_f= f"{args.id_out}.merged.reject"

    # 3) Rearrange → FASTA + gzip
    fa = f"{args.id_out}.merged.match.enh.fa"
    run(f"awk '{{print \">\"$1\"#\"$3\"\\n\"$4}}' {match_f} > {fa}")
    run(f"gzip {fa}")
    gz_fa = fa + ".gz"

    # 4) Minimap2 + samtools
    sam = f"{args.id_out}.merged.match.enh.sam"
    log = f"{args.id_out}.merged.match.enh.log"
    bam = f"{args.id_out}.merged.match.enh.bam"
    run(
        f"minimap2 --for-only -Y --secondary=no -m 10 -n 1 "
        f"-t {args.threads} --end-bonus 12 -O 5 -E 1 -k 10 -2K50m --eqx --cs=short "
        f"-c -a {args.reference_fasta} {gz_fa} > {sam} 2> {log}"
    )
    run(f"samtools view -S -b {sam} > {bam}")

    # 5) SAM2MPRA
    mapped = f"{args.id_out}.merged.match.enh.mapped"
    run(
        f"python3 {args.scripts_dir}/sam2mpra_cs.py -C {sam} -O {args.oligo_alnmismatchrate_cutoff} {mapped}"
    )

    # 6) Sort
    sorted_f = f"{mapped}.barcode.sort"
    run(f"sort -S{args.mem}G -k2 {mapped} > {sorted_f}")

    # 7) Ct_Seq
    ct          = f"{args.id_out}.merged.match.enh.mapped.barcode.ct"
    run(f"python3 {args.scripts_dir}/ct_seq.py {sorted_f} 2 4 > {ct}")

    # 8) Parse / Parse_sat_mut + histogram
    parsed     = f"{args.id_out}.merged.match.enh.mapped.barcode.ct.parsed"
    hist       = f"{args.id_out}.merged.match.enh.mapped.barcode.ct.plothist"
    if args.attributes:
        run(f"python3 {args.scripts_dir}/parse_map.py -S -A {args.attributes} {ct} > {parsed}")
    else:
        run(f"python3 {args.scripts_dir}/parse_map.py {ct} > {parsed}")
    run(
        f"awk '($5==0)' {ct} "
        f"| awk '{{ct[$2]++;cov[$2]+=$4}} END {{for(i in ct) print i\"\\t\"ct[i]\"\\t\"cov[i]}}' > {hist}"
    )

    # 9) Preseq
    hist_in  = f"{args.id_out}.merged.match.enh.mapped.barcode.ct.hist"
    hist_out = f"{args.id_out}.merged.match.enh.mapped.barcode.ct.hist.preseq"
    run(f"awk '{{ct[$4]++}} END {{for(i in ct) print i\"\\t\"ct[i]}}' {ct} | sort -k1n > {hist_in}")
    run(f"preseq lc_extrap -H {hist_in} -o {hist_out} -s 25000000 -n 1000 -e 1000000000")

    # 10) QC plots
    run(
        f"python3 {args.scripts_dir}/mapping_qc_plots.py "
        f"{parsed} {hist} {hist_out} {hist_in} {args.reference_fasta} {args.id_out}"
    )

    # 11) relocate everything into out_dir
    to_move = [
        flash_out, match_f, reject_f, gz_fa,
        sam, log, bam,
        mapped, sorted_f, ct,
        parsed, hist, hist_in, hist_out,
        f"{args.id_out}_barcode_qc.pdf"
    ]
    for fn in to_move:
        run(f"mv {fn} {args.out_dir}/")

if __name__ == "__main__":
    main()
