# Run log

| Date (UTC) | Stage | Command | Result |
|---|---|---|---|
| 2026-10-13 | 0 | `../.venv/bin/python scripts/00_query_redivis.py` (login node, ~1 min) | 10k family 358,372 rows (incl. amendments), 10q family 878,478, 8-K since 2023-12-18 188,038. Flags: 1996 low (EDGAR phase-in ended May 1996), 8-K 2023 partial by design |
| 2026-10-13 | transfer | `globus transfer 2556f515-7a87-407b-a24d-18ed16237588 56ac92ca-0bad-4009-baaa-513525b3e648 --batch batch.txt --sync-level checksum --verify-checksum --label "cyber-distill stage0 test"` | Task fc23d77c-c731-11f1-8d8e-0effcb3df825 SUCCEEDED, 3 files, 9,875 bytes. Created `/scratch/m000106/gsb_hackathon/cyber-distill/{data/final,data/interim,data/teacher,models,config}` with `globus mkdir`. Globus path drops `/scratch` (collection root is `/scratch`) |
| 2026-10-13 | 1a | `sbatch slurm/01_headers.slurm` | Job 749025, 31 tasks (filing years 1996-2026), all COMPLETED in under 2 min each. 9 header errors (all 1996), 0 missing files |
| 2026-10-13 | 1b | `../.venv/bin/python scripts/01_select.py` (login node, ~1 min) | `data/final/filings.parquet`, 324,293 rows: 277,329 annual reports (42,883 companies, FY1996-2025), 46,873 Item 8.01 8-Ks, 58 Item 1.05 8-Ks (57 companies), 49 follow-up 10-Q/10-Ks. Fixes: Item 1.05 appears in headers as `<ITEMS>1.05`; SIC filled from same CIK's other filings (5,579 filled, mostly FY2000) |

The runs above predate the git repository; commit `96f23a0` contains the code that produced them. From here on each row names its commit.
| 2026-10-13 | 2-3 test | `sbatch --array=0 slurm/02_extract.slurm --test-years 1998 2008 2022 --limit 200` (jobs 749123, 749128 failed: look-behind regex, then pickling of pandas rows; fixed) | Job 749135 at `810509d`'s parent: 600 filings, 0 failures, 259,770 paragraphs in 26 s. Then added standalone "Risk Factors", Regulation AB and 1A-not-applicable flags; rerun: 1A found in 85% (2008) and 96% (2022) of expected filings |
| 2026-10-13 | 2-3 test | `sbatch --array=0 slurm/02_extract.slurm --test-years 2024 --limit 200` + 8-K/10-Q spot check | FY2024 non-ABS: 1C 95.6%, 1A 95.7%, Item 7 100%; 8-K item sections (1.05, 8.01, 9.01) correct. Test outputs deleted before the full run |
| 2026-10-13 | 2-3 | `sbatch slurm/02_extract.slurm` at `810509d`; `sbatch --dependency=afterok:749166 slurm/03_check.slurm` | Jobs 749166 (64 tasks) and 749172; results below when finished |
