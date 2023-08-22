# Config files for TrendyQC

## Why

TrendyQC possesses config files to define what tools it can support and perform checks on the MultiQC reports.

For an assay used to create a MultiQC report, we have a specific set of tools that we use since scientists are not going to care about the same QC metrics depending on the assay.

Additionally the fields used in the tools might have been modified to accomodate Python i.e. `%GC` in FastQC became `gc_pct` in the models. The tool level config contain the field names in the MultiQC reports pointing to the model field names.

## Example assay level config

This should contain the assay name as the "first key level" as it is found in the `config_subtitle` field in the `multiqc_data.json` produced by the MultiQC DNAnexus app that we use.

For every assay, the set of tools to use is the fields in the `report_saved_raw_data` field. Those field names point to a 2 element list that contain the actual name of the tool (which will be used to gather the tool config JSON) and if it exists, the subtool i.e. HSMetrics for Picard or SNP for Happy.

```json
{
    "Myeloid": {
        "multiqc_bcl2fastq_bysample": ["bcl2fastq", null],
        "multiqc_fastqc": ["fastqc", null],
        "multiqc_general_stats": ["custom_coverage", null],
        "multiqc_picard_AlignmentSummaryMetrics": ["picard", "alignment_summary_metrics"],
        "multiqc_picard_HsMetrics": ["picard", "hs_metrics"],
        "multiqc_picard_insertSize": ["picard", "insert_size_metrics"],
        "multiqc_samtools_flagstat": ["samtools", null],
        "multiqc_somalier_sex_check": ["somalier", null],
        "multiqc_sompy": ["sompy", null],
        "multiqc_verifybamid": ["verifybamid", null]
    },
    "Cancer Endocrine Neurology": {
        "multiqc_bcl2fastq_bysample": ["bcl2fastq", null],
        "multiqc_fastqc": ["fastqc", null],
        "multiqc_happy_indel_data": ["happy", "indel"],
        "multiqc_happy_snp_data": ["happy", "snp"],
        "multiqc_het-hom_analysis": ["vcfqc", null],
        "multiqc_picard_HsMetrics": ["picard", "hs_metrics"],
        "multiqc_samtools_flagstat": ["samtools", null],
        "multiqc_sentieon_AlignmentSummaryMetrics": ["picard", "alignment_summary_metrics"],
        "multiqc_sentieon_insertSize": ["picard", "insert_size_metrics"],
        "multiqc_somalier_sex_check": ["somalier", null],
        "multiqc_verifybamid": ["verifybamid", null]
    }
}
```

## Example tool level config

As previously mentionned, those config files are named to match the tool names in the assay config. They are used to rename the MultiQC fields to match the fields written in the models for facilitate a later import.

They can have an additional level depending on whether some level of granularity is needed for that tool.

For example:

- Picard
  - HSMetrics
  - insertSize
  - AlignmentSummaryMetrics
- Happy
  - SNP
  - Indels

Example file without granularity:

```json
{
    "total": "total",
    "total_yield": "total_yield",
    "perfectIndex": "perfect_index",
    "yieldQ30": "yield_Q30",
    "qscore_sum": "qscore_sum",
    "R1_yield": "r1_yield",
    "R1_Q30": "r1_Q30",
    "R1_trimmed_bases": "r1_trimmed_bases",
    "R2_yield": "r2_yield",
    "R2_Q30": "r2_Q30",
    "R2_trimmed_bases": "r2_trimmed_bases",
    "percent_Q30": "pct_Q30",
    "percent_perfectIndex": "pct_perfect_index",
    "mean_qscore": "mean_qscore"
}
```

Example file with granularity:

```json
{
    "hs_metrics": {
        "BAIT_SET": "bait_set",
        "BAIT_TERRITORY": "bait_territory",
        "BAIT_DESIGN_EFFICIENCY": "bait_design_efficiency",
        "ON_BAIT_BASES": "on_bait_bases",
        "NEAR_BAIT_BASES": "near_bait_bases",
        "OFF_BAIT_BASES": "off_bait_bases",
        "PCT_SELECTED_BASES": "pct_selected_bases",
        "PCT_OFF_BAIT": "pct_off_bait",
        "ON_BAIT_VS_SELECTED": "on_bait_vs_selected",
        "MEAN_BAIT_COVERAGE": "mean_bait_coverage",
        "PCT_USABLE_BASES_ON_BAIT": "pct_usable_bases_on_bait",
        "PCT_USABLE_BASES_ON_TARGET": "pct_usable_bases_on_target",
        "FOLD_ENRICHMENT": "fold_enrichment",
        "HS_LIBRARY_SIZE": "hs_library_size",
        "HS_PENALTY_10x": "hs_penalty_10x",
        "HS_PENALTY_20x": "hs_penalty_10x",
        "HS_PENALTY_30x": "hs_penalty_30x",
        "HS_PENALTY_40x": "hs_penalty_40x",
        "HS_PENALTY_50x": "hs_penalty_50x",
        "HS_PENALTY_100x": "hs_penalty_100x",
        "TARGET_TERRITORY": "target_territory",
        "GENOME_SIZE": "genome_size",
        "TOTAL_READS": "total_reads",
        "PF_READS": "pf_reads",
        "PF_BASES": "pf_bases",
        "PF_UNIQUE_READS": "pf_unique_reads",
        "PF_UQ_READS_ALIGNED": "pf_uq_reads_aligned",
        "PF_BASES_ALIGNED": "pf_bases_aligned",
        "PF_UQ_BASES_ALIGNED": "pf_uq_bases_aligned",
        "ON_TARGET_BASES": "on_target_bases",
        "PCT_PF_READS": "pct_pf_reads",
        "PCT_PF_UQ_READS": "pct_pf_uq_reads",
        "PCT_PF_UQ_READS_ALIGNED": "pct_pf_uq_reads_aligned",
        "MEAN_TARGET_COVERAGE": "mean_target_coverage",
        "MEDIAN_TARGET_COVERAGE": "median_target_coverage",
        "MAX_TARGET_COVERAGE": "max_target_coverage",
        "MIN_TARGET_COVERAGE": "min_target_coverage",
        "ZERO_CVG_TARGETS_PCT": "zero_cvg_targets_pct",
        "PCT_EXC_DUPE": "pct_exc_dupe",
        "PCT_EXC_ADAPTER": "pct_exc_adapter",
        "PCT_EXC_MAPQ": "pct_exc_mapq",
        "PCT_EXC_BASEQ": "pct_exc_baseq",
        "PCT_EXC_OVERLAP": "pct_exc_overlap",
        "PCT_EXC_OFF_TARGET": "pct_exc_off_target",
        "FOLD_80_BASE_PENALTY": "fold_80_base_penalty",
        "PCT_TARGET_BASES_1X": "pct_target_bases_1x",
        "PCT_TARGET_BASES_2X": "pct_target_bases_2x",
        "PCT_TARGET_BASES_10X": "pct_target_bases_10x",
        "PCT_TARGET_BASES_20X": "pct_target_bases_20x",
        "PCT_TARGET_BASES_30X": "pct_target_bases_30x",
        "PCT_TARGET_BASES_40X": "pct_target_bases_40x",
        "PCT_TARGET_BASES_50X": "pct_target_bases_50x",
        "PCT_TARGET_BASES_100X": "pct_target_bases_100x",
        "AT_DROPOUT": "at_dropout",
        "GC_DROPOUT": "gc_dropout",
        "HET_SNP_SENSITIVITY": "het_snp_sensitivity",
        "HET_SNP_Q": "het_snp_q"
    },
    "alignment_summary_metrics": {
        "CATEGORY": "category",
        "TOTAL_READS": "total_reads",
        "PF_READS": "pf_reads",
        "PCT_PF_READS": "pct_pf_reads",
        "PF_NOISE_READS": "pf_noise_reads",
        "PF_READS_ALIGNED": "pf_reads_aligned",
        "PF_ALIGNED_BASES": "pf_aligned_bases",
        "PF_HQ_ALIGNED_READS": "pf_hq_aligned_reads",
        "PF_HQ_ALIGNED_BASES": "pf_hq_aligned_bases",
        "PF_HQ_ALIGNED_Q20_BASES": "pf_hq_aligned_q20_bases",
        "PF_HQ_MEDIAN_MISMATCHES": "pf_hq_median_mismatches",
        "PF_MISMATCH_RATE": "pf_mismatch_rate",
        "PF_HQ_ERROR_RATE": "pf_hq_error_rate",
        "PF_INDEL_RATE": "pf_indel_rate",
        "MEAN_READ_LENGTH": "mean_read_length",
        "READS_ALIGNED_IN_PAIRS": "reads_aligned_in_pairs",
        "PCT_READS_ALIGNED_IN_PAIRS": "pct_reads_aligned_in_pairs",
        "PF_READS_IMPROPER_PAIRS": "pf_reads_improper_pairs",
        "PCT_PF_READS_IMPROPER_PAIRS": "pct_pf_reads_improper_pairs",
        "BAD_CYCLES": "bad_cycles",
        "STRAND_BALANCE": "strand_balance",
        "PCT_CHIMERAS": "pct_chimeras",
        "PCT_ADAPTER": "pct_adapter"
    },
    "insert_size_metrics": {
        "MEDIAN_INSERT_SIZE": "median_insert_size",
        "MODE_INSERT_SIZE": "mode_insert_size",
        "MEDIAN_ABSOLUTE_DEVIATION": "median_absolute_deviation",
        "MIN_INSERT_SIZE": "min_insert_size",
        "MAX_INSERT_SIZE": "max_insert_size",
        "MEAN_INSERT_SIZE": "mean_insert_size",
        "STANDARD_DEVIATION": "standard_deviation",
        "READ_PAIRS": "read_pairs",
        "PAIR_ORIENTATION": "pair_orientation",
        "WIDTH_OF_10_PERCENT": "width_of_10_pct",
        "WIDTH_OF_20_PERCENT": "width_of_20_pct",
        "WIDTH_OF_30_PERCENT": "width_of_30_pct",
        "WIDTH_OF_40_PERCENT": "width_of_40_pct",
        "WIDTH_OF_50_PERCENT": "width_of_50_pct",
        "WIDTH_OF_60_PERCENT": "width_of_60_pct",
        "WIDTH_OF_70_PERCENT": "width_of_70_pct",
        "WIDTH_OF_80_PERCENT": "width_of_80_pct",
        "WIDTH_OF_90_PERCENT": "width_of_90_pct",
        "WIDTH_OF_99_PERCENT": "width_of_99_pct"
    }
}
```
