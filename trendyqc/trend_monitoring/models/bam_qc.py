from django.db import models


class VerifyBAMid_data(models.Model):
    rg = models.CharField(max_length=10)
    chip_id = models.CharField(max_length=10, null=True)
    nb_snps = models.IntegerField()
    nb_reads = models.IntegerField()
    avg_dp = models.FloatField()
    freemix = models.FloatField()
    freelk1 = models.FloatField()
    freelk0 = models.FloatField()
    free_rh = models.CharField(max_length=10, null=True)
    free_ra = models.CharField(max_length=10, null=True)
    chipmix = models.CharField(max_length=10, null=True)
    chiplk1 = models.CharField(max_length=10, null=True)
    chiplk0 = models.CharField(max_length=10, null=True)
    chip_rh = models.CharField(max_length=10, null=True)
    chip_ra = models.CharField(max_length=10, null=True)
    dpref = models.CharField(max_length=10, null=True)
    rdphet = models.CharField(max_length=10, null=True)
    rdpalt = models.CharField(max_length=10, null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "verifybamid_data"


class Samtools_data(models.Model):
    total_passed = models.IntegerField(null=True)
    total_failed = models.IntegerField(null=True)
    secondary_passed = models.IntegerField(null=True)
    secondary_failed = models.IntegerField(null=True)
    supplementary_passed = models.IntegerField(null=True)
    supplementary_failed = models.IntegerField(null=True)
    duplicates_passed = models.IntegerField(null=True)
    duplicates_failed = models.IntegerField(null=True)
    mapped_passed = models.IntegerField(null=True)
    mapped_failed = models.IntegerField(null=True)
    mapped_passed_pct = models.FloatField(null=True)
    mapped_failed_pct = models.FloatField(null=True)
    paired_in_sequencing_passed = models.IntegerField(null=True)
    paired_in_sequencing_failed = models.IntegerField(null=True)
    r1_passed = models.IntegerField(null=True)
    r1_failed = models.IntegerField(null=True)
    r2_passed = models.IntegerField(null=True)
    r2_failed = models.IntegerField(null=True)
    properly_paired_passed = models.IntegerField(null=True)
    properly_paired_failed = models.IntegerField(null=True)
    properly_paired_passed_pct = models.FloatField(null=True)
    properly_paired_failed_pct = models.FloatField(null=True)
    with_itself_and_mate_mapped_passed = models.IntegerField(null=True)
    with_itself_and_mate_mapped_failed = models.IntegerField(null=True)
    singletons_passed = models.IntegerField(null=True)
    singletons_failed = models.IntegerField(null=True)
    singletons_passed_pct = models.FloatField(null=True)
    singletons_failed_pct = models.FloatField(null=True)
    with_mate_mapped_to_a_different_chr_passed = models.IntegerField(null=True)
    with_mate_mapped_to_a_different_chr_failed = models.IntegerField(null=True)
    with_mate_mapped_to_a_different_chr_mapQ_over_5_passed = (
        models.IntegerField(null=True)
    )
    with_mate_mapped_to_a_different_chr_mapQ_over_5_failed = (
        models.IntegerField(null=True)
    )
    flagstat_total = models.IntegerField(null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "samtools_data"


class Custom_coverage(models.Model):
    cov_200x = models.FloatField(null=True)
    cov_250x = models.FloatField(null=True)
    cov_300x = models.FloatField(null=True)
    cov_500x = models.FloatField(null=True)
    cov_1000x = models.FloatField(null=True)
    usable_unique_bases_on_target = models.FloatField(null=True)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "custom_coverage"


class Picard(models.Model):
    hs_metrics = models.ForeignKey(
        "HS_metrics", on_delete=models.DO_NOTHING, blank=True, null=True
    )
    alignment_summary_metrics = models.ForeignKey(
        "Alignment_summary_metrics",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    base_distribution_by_cycle_metrics_1st_lane_R1 = models.ForeignKey(
        "Base_distribution_by_cycle_metrics",
        related_name="base_distribution_by_cycle_metrics_1st_lane_R1",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    base_distribution_by_cycle_metrics_1st_lane_R2 = models.ForeignKey(
        "Base_distribution_by_cycle_metrics",
        related_name="base_distribution_by_cycle_metrics_1st_lane_R2",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    base_distribution_by_cycle_metrics_2nd_lane_R1 = models.ForeignKey(
        "Base_distribution_by_cycle_metrics",
        related_name="base_distribution_by_cycle_metrics_2nd_lane_R1",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    base_distribution_by_cycle_metrics_2nd_lane_R2 = models.ForeignKey(
        "Base_distribution_by_cycle_metrics",
        related_name="base_distribution_by_cycle_metrics_2nd_lane_R2",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    gc_bias_metrics = models.ForeignKey(
        "GC_bias_metrics", on_delete=models.DO_NOTHING, blank=True, null=True,
    )
    insert_size_metrics = models.ForeignKey(
        "Insert_size_metrics",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    quality_yield_metrics = models.ForeignKey(
        "Quality_yield_metrics",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    pcr_metrics = models.ForeignKey(
        "PCR_metrics", on_delete=models.DO_NOTHING, blank=True, null=True,
    )
    duplication_metrics = models.ForeignKey(
        "Duplication_metrics",
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
    )
    rnaseq_metrics = models.ForeignKey(
        "RNAseq_metrics", on_delete=models.DO_NOTHING, blank=True, null=True,
    )

    class Meta:
        app_label = "trend_monitoring"
        db_table = "picard"


class HS_metrics(models.Model):
    bait_set = models.CharField(max_length=10)
    bait_territory = models.FloatField()
    bait_design_efficiency = models.FloatField()
    on_bait_bases = models.FloatField()
    near_bait_bases = models.FloatField()
    off_bait_bases = models.FloatField()
    pct_selected_bases = models.FloatField()
    pct_off_bait = models.FloatField()
    on_bait_vs_selected = models.FloatField(null=True)
    mean_bait_coverage = models.FloatField()
    pct_usable_bases_on_bait = models.FloatField()
    pct_usable_bases_on_target = models.FloatField()
    fold_enrichment = models.FloatField()
    hs_library_size = models.FloatField(null=True)
    hs_penalty_10x = models.FloatField()
    hs_penalty_20x = models.FloatField()
    hs_penalty_30x = models.FloatField()
    hs_penalty_40x = models.FloatField()
    hs_penalty_50x = models.FloatField()
    hs_penalty_100x = models.FloatField()
    target_territory = models.FloatField()
    genome_size = models.FloatField()
    total_reads = models.FloatField()
    pf_reads = models.FloatField()
    pf_bases = models.FloatField()
    pf_unique_reads = models.FloatField()
    pf_uq_reads_aligned = models.FloatField()
    pf_bases_aligned = models.FloatField()
    pf_uq_bases_aligned = models.FloatField()
    on_target_bases = models.FloatField()
    pct_pf_reads = models.FloatField()
    pct_pf_uq_reads = models.FloatField()
    pct_pf_uq_reads_aligned = models.FloatField()
    mean_target_coverage = models.FloatField()
    median_target_coverage = models.FloatField()
    max_target_coverage = models.FloatField()
    min_target_coverage = models.FloatField()
    zero_cvg_targets_pct = models.FloatField()
    pct_exc_dupe = models.FloatField()
    pct_exc_adapter = models.FloatField()
    pct_exc_mapq = models.FloatField()
    pct_exc_baseq = models.FloatField()
    pct_exc_overlap = models.FloatField()
    pct_exc_off_target = models.FloatField()
    fold_80_base_penalty = models.FloatField(null=True)
    pct_target_bases_1x = models.FloatField()
    pct_target_bases_2x = models.FloatField()
    pct_target_bases_10x = models.FloatField()
    pct_target_bases_20x = models.FloatField()
    pct_target_bases_30x = models.FloatField()
    pct_target_bases_40x = models.FloatField()
    pct_target_bases_50x = models.FloatField()
    pct_target_bases_100x = models.FloatField()
    at_dropout = models.FloatField()
    gc_dropout = models.FloatField()
    het_snp_sensitivity = models.FloatField()
    het_snp_q = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "hs_metrics"


class Alignment_summary_metrics(models.Model):
    category = models.CharField(max_length=10)
    total_reads = models.FloatField()
    pf_reads = models.FloatField()
    pct_pf_reads = models.FloatField()
    pf_noise_reads = models.FloatField()
    pf_reads_aligned = models.FloatField()
    pct_pf_reads_aligned = models.FloatField()
    pf_aligned_bases = models.FloatField()
    pf_hq_aligned_reads = models.FloatField()
    pf_hq_aligned_bases = models.FloatField()
    pf_hq_aligned_q20_bases = models.FloatField()
    pf_hq_median_mismatches = models.FloatField()
    pf_mismatch_rate = models.FloatField()
    pf_hq_error_rate = models.FloatField()
    pf_indel_rate = models.FloatField()
    mean_read_length = models.FloatField()
    reads_aligned_in_pairs = models.FloatField()
    pct_reads_aligned_in_pairs = models.FloatField()
    pf_reads_improper_pairs = models.FloatField(null=True)
    pct_pf_reads_improper_pairs = models.FloatField(null=True)
    bad_cycles = models.FloatField()
    strand_balance = models.FloatField()
    pct_chimeras = models.FloatField()
    pct_adapter = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "alignment_summary_metrics"


class Base_distribution_by_cycle_metrics(models.Model):
    lane = models.CharField(max_length=20)
    sample_read = models.CharField(max_length=20)
    sum_pct_a = models.FloatField()
    sum_pct_c = models.FloatField()
    sum_pct_g = models.FloatField()
    sum_pct_t = models.FloatField()
    sum_pct_n = models.FloatField()
    cycle_count = models.IntegerField()
    mean_pct_a = models.FloatField()
    mean_pct_c = models.FloatField()
    mean_pct_g = models.FloatField()
    mean_pct_t = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "base_distribution_by_cycle_metrics"


class GC_bias_metrics(models.Model):
    accumulation_level = models.CharField(max_length=20)
    reads_used = models.CharField(max_length=10)
    window_size = models.IntegerField()
    total_clusters = models.IntegerField()
    aligned_reads = models.IntegerField()
    at_dropout = models.FloatField()
    gc_dropout = models.FloatField()
    gc_nc_0_19 = models.FloatField()
    gc_nc_20_39 = models.FloatField()
    gc_nc_40_59 = models.FloatField()
    gc_nc_60_79 = models.FloatField()
    gc_nc_80_100 = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "gc_bias_metrics"


class Insert_size_metrics(models.Model):
    median_insert_size = models.FloatField()
    mode_insert_size = models.FloatField(null=True)
    median_absolute_deviation = models.FloatField()
    min_insert_size = models.FloatField()
    max_insert_size = models.FloatField()
    mean_insert_size = models.FloatField()
    standard_deviation = models.FloatField(null=True)
    read_pairs = models.FloatField()
    pair_orientation = models.CharField(max_length=10)
    width_of_10_pct = models.FloatField()
    width_of_20_pct = models.FloatField()
    width_of_30_pct = models.FloatField()
    width_of_40_pct = models.FloatField()
    width_of_50_pct = models.FloatField()
    width_of_60_pct = models.FloatField()
    width_of_70_pct = models.FloatField()
    width_of_80_pct = models.FloatField()
    width_of_90_pct = models.FloatField()
    width_of_99_pct = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "insert_size_metrics"


class Quality_yield_metrics(models.Model):
    total_reads = models.IntegerField()
    pf_reads = models.IntegerField()
    read_length = models.IntegerField()
    total_bases = models.IntegerField()
    pf_bases = models.IntegerField()
    q20_bases = models.IntegerField()
    pf_q20_bases = models.IntegerField()
    q30_bases = models.IntegerField()
    pf_q30_bases = models.IntegerField()
    q20_equivalent_yield = models.FloatField()
    pf_q20_equivalent_yield = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "quality_yield_metrics"


class PCR_metrics(models.Model):
    custom_amplicon_set = models.CharField(max_length=20)
    amplicon_territory = models.FloatField()
    on_amplicon_bases = models.FloatField()
    near_amplicon_bases = models.FloatField()
    off_amplicon_bases = models.FloatField()
    pct_amplified_bases = models.FloatField()
    pct_off_amplicon = models.FloatField()
    on_amplicon_vs_selected = models.FloatField(null=True)
    mean_amplicon_cov = models.FloatField()
    fold_enrichment = models.FloatField()
    pf_selected_pairs = models.FloatField()
    pf_selected_unique_pairs = models.FloatField()
    on_target_from_pair_bases = models.FloatField()
    target_territory = models.FloatField()
    genome_size = models.FloatField()
    total_reads = models.FloatField()
    pf_reads = models.FloatField()
    pf_bases = models.FloatField()
    pf_unique_reads = models.FloatField()
    pf_uq_reads_aligned = models.FloatField()
    pf_bases_aligned = models.FloatField()
    pf_uq_bases_aligned = models.FloatField()
    on_target_bases = models.FloatField()
    pct_pf_reads = models.FloatField()
    pct_pf_uq_reads = models.FloatField()
    pct_pf_uq_reads_aligned = models.FloatField()
    mean_target_cov = models.FloatField()
    median_target_cov = models.FloatField()
    max_target_cov = models.FloatField()
    min_target_cov = models.FloatField()
    zero_cvg_targets_pct = models.FloatField()
    pct_exc_dupe = models.FloatField()
    pct_exc_adapter = models.FloatField()
    pct_exc_mapq = models.FloatField()
    pct_exc_baseq = models.FloatField()
    pct_exc_overlap = models.FloatField()
    pct_exc_off_target = models.FloatField()
    fold_80_base_penalty = models.FloatField(null=True)
    pct_target_bases_1x = models.FloatField()
    pct_target_bases_2x = models.FloatField()
    pct_target_bases_10x = models.FloatField()
    pct_target_bases_20x = models.FloatField()
    pct_target_bases_30x = models.FloatField()
    pct_target_bases_40x = models.FloatField()
    pct_target_bases_50x = models.FloatField()
    pct_target_bases_100x = models.FloatField()
    at_dropout = models.FloatField()
    gc_dropout = models.FloatField()
    het_snp_sensitivity = models.FloatField()
    het_snp_q = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "pcr_metrics"


class Duplication_metrics(models.Model):
    unpaired_reads_examined = models.FloatField()
    read_pairs_examined = models.FloatField()
    secondary_or_suplementary_rds = models.FloatField()
    unmapped_reads = models.FloatField()
    unpaired_read_duplicates = models.FloatField()
    read_pair_duplicates = models.FloatField()
    read_pair_optical_duplicates = models.FloatField()
    pct_duplication = models.FloatField()
    estimated_library_size = models.FloatField()
    reads_in_duplicate_pairs = models.FloatField()
    reads_in_unique_pairs = models.FloatField()
    reads_in_unique_unpaired = models.FloatField()
    reads_in_duplicate_pairs_optical = models.FloatField()
    reads_in_duplicate_pairs_nonoptical = models.FloatField()
    reads_in_duplicate_unpaired = models.FloatField()
    reads_unmapped = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "duplication_metrics"


class RNAseq_metrics(models.Model):
    pf_bases = models.FloatField()
    pf_aligned_bases = models.FloatField()
    ribosomal_bases = models.FloatField(null=True)
    coding_bases = models.FloatField()
    utr_bases = models.FloatField()
    intronic_bases = models.FloatField()
    intergenic_bases = models.FloatField()
    ignored_reads = models.FloatField()
    correct_strand_reads = models.FloatField()
    incorrect_strand_reads = models.FloatField()
    num_r1_transcript_strand_reads = models.FloatField()
    num_r2_transcript_strand_reads = models.FloatField()
    num_unexplained_reads = models.FloatField()
    pct_r1_transcript_strand_reads = models.FloatField()
    pct_r2_transcript_strand_reads = models.FloatField()
    pct_ribosomal_bases = models.FloatField(null=True)
    pct_coding_bases = models.FloatField()
    pct_utr_bases = models.FloatField()
    pct_intronic_bases = models.FloatField()
    pct_intergenic_bases = models.FloatField()
    pct_mrna_bases = models.FloatField()
    pct_usable_bases = models.FloatField()
    pct_correct_strand_reads = models.FloatField()
    median_cv_coverage = models.FloatField()
    median_5prime_bias = models.FloatField()
    median_3prime_bias = models.FloatField()
    median_5prime_to_3prime_bias = models.FloatField()
    pf_not_aligned_bases = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "rnaseq_metrics"


class RNA_seqc(models.Model):
    mapping_rate = models.FloatField()
    unique_rate_of_mapped = models.FloatField()
    duplicate_rate_of_mapped = models.FloatField()
    duplicate_rate_of_mapped_excluding_globins = models.FloatField()
    base_mismatch = models.FloatField()
    end_1_mapping_rate = models.FloatField()
    end_2_mapping_rate = models.FloatField()
    end_1_mismatch_rate = models.FloatField(null=True)
    end_2_mismatch_rate = models.FloatField(null=True)
    expression_profiling_efficiency = models.FloatField()
    high_quality_rate = models.FloatField()
    exonic_rate = models.FloatField()
    intronic_rate = models.FloatField()
    intergenic_rate = models.FloatField()
    intragenic_rate = models.FloatField()
    ambiguous_alignment_rate = models.FloatField()
    high_quality_exonic_rate = models.FloatField()
    high_quality_intronic_rate = models.FloatField()
    high_quality_intergenic_rate = models.FloatField()
    high_quality_intragenic_rate = models.FloatField()
    high_quality_ambiguous_alignment_rate = models.FloatField()
    discard_rate = models.FloatField()
    rrna_rate = models.FloatField()
    end_1_sense_rate = models.FloatField()
    end_2_sense_rate = models.FloatField()
    avg_splits_per_read = models.FloatField()
    alternative_alignments = models.FloatField()
    chimeric_reads = models.FloatField()
    chimeric_alignment_rate = models.FloatField()
    duplicate_reads = models.FloatField()
    end_1_antisense = models.FloatField()
    end_2_antisense = models.FloatField()
    end_1_bases = models.FloatField()
    end_2_bases = models.FloatField()
    end_1_mapped_reads = models.FloatField()
    end_2_mapped_reads = models.FloatField()
    end_1_mismatches = models.FloatField()
    end_2_mismatches = models.FloatField()
    end_1_sense = models.FloatField()
    end_2_sense = models.FloatField()
    exonic_reads = models.FloatField()
    failed_vendor_qc = models.FloatField()
    high_quality_reads = models.FloatField()
    intergenic_reads = models.FloatField()
    intragenic_reads = models.FloatField()
    ambiguous_reads = models.FloatField()
    intronic_reads = models.FloatField()
    low_mapping_quality = models.FloatField()
    low_quality_reads = models.FloatField()
    mapped_duplicate_reads = models.FloatField()
    mapped_reads = models.FloatField()
    mapped_unique_reads = models.FloatField()
    mismatched_bases = models.FloatField()
    non_globin_reads = models.FloatField()
    non_globin_duplicate_reads = models.FloatField()
    reads_used_for_intron_exon_counts = models.FloatField()
    rrna_reads = models.FloatField()
    total_bases = models.FloatField()
    total_mapped_pairs = models.FloatField()
    total_read_number = models.FloatField()
    unique_mapping_vendor_qc_passed_reads = models.FloatField()
    unpaired_reads = models.FloatField()
    read_length = models.FloatField()
    genes_detected = models.FloatField()
    estimated_library_complexity = models.FloatField()
    genes_used_in_three_prime_bias = models.FloatField()
    mean_three_prime_bias = models.FloatField()
    median_three_prime_bias = models.FloatField()
    three_prime_bias_std = models.FloatField()
    three_prime_bias_mad_std = models.FloatField()
    three_prime_bias_25th_percentile = models.FloatField()
    three_prime_bias_75th_percentile = models.FloatField()
    average_fragment_length = models.FloatField()
    fragment_length_median = models.FloatField()
    fragment_length_std = models.FloatField()
    fragment_length_mad_std = models.FloatField()
    median_of_avg_transcript_coverage = models.FloatField()
    median_of_transcript_coverage_std = models.FloatField()
    median_of_transcript_coverage_cv = models.FloatField()
    median_exon_cv = models.FloatField()
    exon_cv_mad = models.FloatField()
    sample = models.CharField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "rna_seqc"
