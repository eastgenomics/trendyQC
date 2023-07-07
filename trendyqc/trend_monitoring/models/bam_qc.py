from django.db import models


class VerifyBAMid_data(models.Model):
    rg = models.CharField(max_length=10)
    chip_id = models.CharField(max_length=10)
    nb_snps = models.IntegerField()
    nb_reads = models.IntegerField()
    avg_dp = models.FloatField()
    freemix = models.FloatField()
    freelk1 = models.FloatField()
    freelk0 = models.FloatField()
    free_rh = models.CharField(max_length=10)
    free_ra = models.CharField(max_length=10)
    chipmix = models.CharField(max_length=10)
    chiplk1 = models.CharField(max_length=10)
    chiplk0 = models.CharField(max_length=10)
    chip_rh = models.CharField(max_length=10)
    chip_ra = models.CharField(max_length=10)
    dpref = models.CharField(max_length=10)
    rdphet = models.CharField(max_length=10)
    rdpalt = models.CharField(max_length=10)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "verifybamid_data"


class Samtools_data(models.Model):
    total_passed = models.IntegerField()
    total_failed = models.IntegerField()
    secondary_passed = models.IntegerField()
    secondary_failed = models.IntegerField()
    supplementary_passed = models.IntegerField()
    supplementary_failed = models.IntegerField()
    duplicates_passed = models.IntegerField()
    duplicated_failed = models.IntegerField()
    mapped_failed = models.IntegerField()
    mapped_passed_pct = models.FloatField()
    mapped_failed_pct = models.FloatField()
    paired_in_sequencing_passed = models.IntegerField()
    paired_in_sequencing_failed = models.IntegerField()
    read1_passed = models.IntegerField()
    read1_failed = models.IntegerField()
    read2_passed = models.IntegerField()
    read2_failed = models.IntegerField()
    properly_paired_passed = models.IntegerField()
    properly_paired_failed = models.IntegerField()
    properly_paired_passed_pct = models.FloatField()
    properly_paired_failed_pct = models.FloatField()
    with_itself_and_mate_mapped_passed = models.IntegerField()
    with_itself_and_mate_mapped_failed = models.IntegerField()
    singletons_passed = models.IntegerField()
    singletons_failed = models.IntegerField()
    singletons_passed_pct = models.FloatField()
    singletons_failed_pct = models.FloatField()
    with_mate_mapped_to_a_different_chr_passed = models.IntegerField()
    with_mate_mapped_to_a_different_chr_failed = models.IntegerField()
    with_mate_mapped_to_a_different_chr_mapQ_over_5_passed = models.IntegerField()
    with_mate_mapped_to_a_different_chr_mapQ_over_5_failed = models.IntegerField()
    flagstat_total = models.IntegerField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "samtools_data"


class Picard(models.Model):
    hs_metrics = models.ForeignKey("Picard_hs_metrics", on_delete=models.DO_NOTHING)
    alignment_summary_metrics = models.ForeignKey(
        "Picard_alignment_summary_metrics", on_delete=models.DO_NOTHING
    )
    base_distribution_by_cycle_metrics = models.ForeignKey(
        "Picard_base_distribution_by_cycle_metrics",
        on_delete=models.DO_NOTHING
    )
    gc_bias_metrics = models.ForeignKey(
        "Picard_gc_bias_metrics", on_delete=models.DO_NOTHING
    )
    insert_size_metrics = models.ForeignKey(
        "Picard_insert_size_metrics", on_delete=models.DO_NOTHING
    )
    quality_yield_metrics = models.ForeignKey(
        "Picard_quality_yield_metrics", on_delete=models.DO_NOTHING
    )

    class Meta:
        app_label = "trend_monitoring"
        db_table = "picard"


class Picard_hs_metrics(models.Model):
    bait_set = models.CharField(max_length=10)
    genome_size = models.FloatField()
    bait_territory = models.FloatField()
    target_territory = models.FloatField()
    bait_design_efficiency = models.FloatField()
    total_reads = models.FloatField()
    pf_reads = models.FloatField()
    pf_unique_reads = models.FloatField()
    pct_pf_reads = models.FloatField()
    pct_pf_uq_reads = models.FloatField()
    pf_uq_reads_aligned = models.FloatField()
    pct_pf_uq_reads_aligned = models.FloatField()
    pf_bases_aligned = models.FloatField()
    pf_uq_bases_aligned = models.FloatField()
    on_bait_bases = models.FloatField()
    near_bait_bases = models.FloatField()
    off_bait_bases = models.FloatField()
    on_target_bases = models.FloatField()
    mean_bait_coverage = models.FloatField()
    mean_target_coverage = models.FloatField()
    median_target_coverage = models.FloatField()
    max_target_coverage = models.FloatField()
    pct_usable_bases_on_bait = models.FloatField()
    pct_usable_bases_on_target = models.FloatField()
    fold_enrichment = models.FloatField()
    zero_cvg_targets_pct = models.FloatField()
    pct_exc_dupe = models.FloatField()
    pct_exc_mapq = models.FloatField()
    pct_exc_baseq = models.FloatField()
    pct_exc_overlap = models.FloatField()
    pct_exc_off_target = models.FloatField()
    fold_80_base_penalty = models.FloatField()
    pct_target_bases_1x = models.FloatField()
    pct_target_bases_2x = models.FloatField()
    pct_target_bases_10x = models.FloatField()
    pct_target_bases_20x = models.FloatField()
    pct_target_bases_30x = models.FloatField()
    pct_target_bases_40x = models.FloatField()
    pct_target_bases_50x = models.FloatField()
    pct_target_bases_100x = models.FloatField()
    hs_library_size = models.FloatField()
    hs_penalty_10x = models.FloatField()
    hs_penalty_20x = models.FloatField()
    hs_penalty_30x = models.FloatField()
    hs_penalty_40x = models.FloatField()
    hs_penalty_50x = models.FloatField()
    hs_penalty_100x = models.FloatField()
    at_dropout = models.FloatField()
    gc_dropout = models.FloatField()
    het_snp_sensitivity = models.FloatField()
    het_snp_q = models.FloatField()
    sample = models.CharField(max_length=10)
    library = models.CharField(max_length=10)
    read_group = models.CharField(max_length=10)

    class Meta:
        app_label = "trend_monitoring"
        db_table = "picard_hs_metrics"


class Picard_alignment_summary_metrics(models.Model):
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
    bad_cycles = models.FloatField()
    strand_balance = models.FloatField()
    pct_chimeras = models.FloatField()
    pct_adapter = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "picard_alignment_summary_metrics"


class Picard_base_distribution_by_cycle_metrics(models.Model):
    read_end = models.CharField(max_length=5)
    cycle = models.IntegerField()
    pct_a = models.FloatField()
    pct_c = models.FloatField()
    pct_g = models.FloatField()
    pct_t = models.FloatField()
    pct_n = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "picard_base_distribution_by_cycle_metrics"


class Picard_gc_bias_metrics(models.Model):
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
        db_table = "picard_gc_bias_metrics"


class Picard_insert_size_metrics(models.Model):
    median_insert_size = models.FloatField()
    median_absolute_deviation = models.FloatField()
    min_insert_size = models.FloatField()
    max_insert_size = models.FloatField()
    mean_insert_size = models.FloatField()
    standard_deviation = models.FloatField()
    read_pairs = models.FloatField()
    pair_orientation = models.CharField(max_length=5)
    width_of_10_percent = models.FloatField()
    width_of_20_percent = models.FloatField()
    width_of_30_percent = models.FloatField()
    width_of_40_percent = models.FloatField()
    width_of_50_percent = models.FloatField()
    width_of_60_percent = models.FloatField()
    width_of_70_percent = models.FloatField()
    width_of_80_percent = models.FloatField()
    width_of_90_percent = models.FloatField()
    width_of_99_percent = models.FloatField()

    class Meta:
        app_label = "trend_monitoring"
        db_table = "picard_insert_size_metrics"


class Picard_quality_yield_metrics(models.Model):
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
        db_table = "picard_quality_yield_metrics"